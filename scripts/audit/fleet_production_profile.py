#!/usr/bin/env python3
"""Perfil agregado y estrictamente read-only de Fleet en PostgreSQL legacy.

Uso productivo solo con una cuenta autorizada de solo lectura. Las
credenciales se reciben por entorno y nunca se escriben en salida o errores.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|TRUNCATE|ALTER|DROP|CREATE|GRANT|REVOKE|VACUUM|ANALYZE|CALL|COPY)\b",
    re.IGNORECASE,
)
ALLOWED_START = re.compile(r"^\s*(SELECT|WITH|SHOW)\b", re.IGNORECASE)
EXPLICIT_PII_COLUMN = re.compile(
    r"\b(dni|ruc|nroplaca|nombres|apellidos|direccion|telefono|correo|email)\b",
    re.IGNORECASE,
)
SELECT_ALL = re.compile(r"\bSELECT\s+\*", re.IGNORECASE)

BEGIN_READ_ONLY_SQL = "BEGIN READ ONLY"
ROLLBACK_SQL = "ROLLBACK"
TIMEOUT_SQL = "SELECT set_config('statement_timeout', %s, true)"
METADATA_SQL = "SELECT current_database() AS database, CURRENT_DATE AS execution_date"


@dataclass(frozen=True)
class Query:
    name: str
    sql: str


QUERIES = (
    Query(
        "entity_profile",
        """
        WITH profile(entity, total, distinct_pk, null_pk, min_date, max_date) AS (
            SELECT 'empresa', COUNT(*), COUNT(DISTINCT idempresa), COUNT(*) FILTER (WHERE idempresa IS NULL), NULL::date, NULL::date FROM public.empresa
            UNION ALL SELECT 'sucursal', COUNT(*), COUNT(DISTINCT idsucursal), COUNT(*) FILTER (WHERE idsucursal IS NULL), NULL::date, NULL::date FROM public.sucursal
            UNION ALL SELECT 'personal', COUNT(*), COUNT(DISTINCT idpersonal), COUNT(*) FILTER (WHERE idpersonal IS NULL), MIN(fechaingreso), MAX(fechaingreso) FROM public.personal
            UNION ALL SELECT 'vehiculo', COUNT(*), COUNT(DISTINCT idvehiculo), COUNT(*) FILTER (WHERE idvehiculo IS NULL), MIN(fechareg::date), MAX(fechareg::date) FROM public.vehiculo
            UNION ALL SELECT 'propietario', COUNT(*), COUNT(DISTINCT idpropietario), COUNT(*) FILTER (WHERE idpropietario IS NULL), MIN(fechaingreso), MAX(fechaingreso) FROM public.propietario
            UNION ALL SELECT 'transportista', COUNT(*), COUNT(DISTINCT idtransportista), COUNT(*) FILTER (WHERE idtransportista IS NULL), NULL::date, NULL::date FROM public.transportista
            UNION ALL SELECT 'recorridos', COUNT(*), COUNT(DISTINCT idrecorrido), COUNT(*) FILTER (WHERE idrecorrido IS NULL), NULL::date, NULL::date FROM public.recorridos
            UNION ALL SELECT 'public.lineas', COUNT(*), COUNT(DISTINCT idlinea), COUNT(*) FILTER (WHERE idlinea IS NULL), NULL::date, NULL::date FROM public.lineas
            UNION ALL SELECT 'comercial.linea', COUNT(*), COUNT(DISTINCT idlinea), COUNT(*) FILTER (WHERE idlinea IS NULL), NULL::date, NULL::date FROM comercial.linea
            UNION ALL SELECT 'manifiesto', COUNT(*), COUNT(DISTINCT idmanifiesto), COUNT(*) FILTER (WHERE idmanifiesto IS NULL), MIN(documentofecha), MAX(documentofecha) FROM transportes.manifiesto
            UNION ALL SELECT 'papeleta', COUNT(*), COUNT(DISTINCT idpapeleta), COUNT(*) FILTER (WHERE idpapeleta IS NULL), MIN(documentofecha), MAX(documentofecha) FROM administrativo.papeleta
            UNION ALL SELECT 'cliente', COUNT(*), COUNT(DISTINCT idcliente), COUNT(*) FILTER (WHERE idcliente IS NULL), MIN(fechareg), MAX(fechareg) FROM public.cliente
        )
        SELECT entity, total, distinct_pk, null_pk,
               total - distinct_pk - null_pk AS duplicate_pk, min_date, max_date
        FROM profile ORDER BY entity
        """,
    ),
    Query(
        "state_distribution",
        """
        SELECT entity, state, quantity FROM (
            SELECT 'vehiculo' entity, COALESCE(estado::text, '<NULL>') state, COUNT(*) quantity FROM public.vehiculo GROUP BY estado
            UNION ALL SELECT 'propietario', COALESCE(estado::text, '<NULL>'), COUNT(*) FROM public.propietario GROUP BY estado
            UNION ALL SELECT 'transportista', COALESCE(estado::text, '<NULL>'), COUNT(*) FROM public.transportista GROUP BY estado
            UNION ALL SELECT 'recorridos', COALESCE(estado::text, '<NULL>'), COUNT(*) FROM public.recorridos GROUP BY estado
            UNION ALL SELECT 'public.lineas', COALESCE(estado::text, '<NULL>'), COUNT(*) FROM public.lineas GROUP BY estado
            UNION ALL SELECT 'comercial.linea', COALESCE(estado::text, '<NULL>'), COUNT(*) FROM comercial.linea GROUP BY estado
            UNION ALL SELECT 'papeleta.estado', COALESCE(estado::text, '<NULL>'), COUNT(*) FROM administrativo.papeleta GROUP BY estado
            UNION ALL SELECT 'papeleta.estadopago', COALESCE(estadopago::text, '<NULL>'), COUNT(*) FROM administrativo.papeleta GROUP BY estadopago
        ) states ORDER BY entity, state
        """,
    ),
    Query(
        "vehicle_summary",
        """
        SELECT COUNT(*) total,
               COUNT(*) FILTER (WHERE estado = 1) active,
               COUNT(*) FILTER (WHERE estado IS DISTINCT FROM 1) not_active,
               MIN(fechareg::date) min_registration_date,
               MAX(fechareg::date) max_registration_date,
               COUNT(*) FILTER (WHERE idpropietario IS NOT NULL) with_owner,
               COUNT(*) FILTER (WHERE idclase IS NOT NULL) with_class,
               COUNT(*) FILTER (WHERE idmarca IS NOT NULL) with_brand,
               COUNT(*) FILTER (WHERE idlinea IS NOT NULL AND idlinea <> 0) with_line,
               COUNT(*) FILTER (WHERE idsucursal_fin IS NOT NULL) with_branch_fin
        FROM public.vehiculo
        """,
    ),
    Query(
        "vehicle_model_shape",
        """
        SELECT COUNT(*) total,
               COUNT(*) FILTER (WHERE modelo IS NULL OR BTRIM(modelo) = '') null_or_empty,
               COUNT(DISTINCT NULLIF(BTRIM(modelo), '')) distinct_nonempty,
               COUNT(*) FILTER (WHERE idcarroceria IS NOT NULL AND idcarroceria <> 0) with_body_type_id,
               COUNT(*) FILTER (WHERE carroceria IS NOT NULL AND BTRIM(carroceria) <> '') with_body_type_text
        FROM public.vehiculo
        """,
    ),
    Query(
        "catalog_inventory",
        """
        SELECT table_schema, table_name,
               CASE WHEN table_type = 'VIEW' THEN 'VIEW' ELSE 'TABLE' END object_type
        FROM information_schema.tables
        WHERE (table_schema, table_name) IN (
            ('public', 'clase'), ('public', 'color'), ('public', 'marca'),
            ('public', 'v_color'), ('public', 'v_marca'), ('public', 'lineas'),
            ('comercial', 'marca'), ('comercial', 'linea'),
            ('transportes', 'vehiculo_carroceria'),
            ('transportes', 'vehiculo_clase'), ('transportes', 'vehiculo_color'),
            ('transportes', 'vehiculo_marca'), ('transportes', 'vehiculo_modelo')
        )
        ORDER BY table_schema, table_name
        """,
    ),
    Query(
        "catalog_counts",
        """
        SELECT catalog, total, active FROM (
            SELECT 'public.clase' catalog, COUNT(*) total, COUNT(*) FILTER (WHERE estado = 1) active FROM public.clase
            UNION ALL SELECT 'public.color', COUNT(*), COUNT(*) FILTER (WHERE estado = 1) FROM public.color
            UNION ALL SELECT 'public.marca', COUNT(*), COUNT(*) FILTER (WHERE estado = 1) FROM public.marca
            UNION ALL SELECT 'public.lineas', COUNT(*), COUNT(*) FILTER (WHERE estado = 1) FROM public.lineas
            UNION ALL SELECT 'comercial.marca', COUNT(*), COUNT(*) FILTER (WHERE estado = 1) FROM comercial.marca
            UNION ALL SELECT 'comercial.linea', COUNT(*), COUNT(*) FILTER (WHERE estado = 1) FROM comercial.linea
            UNION ALL SELECT 'transportes.vehiculo_carroceria', COUNT(*), COUNT(*) FILTER (WHERE estado = 1) FROM transportes.vehiculo_carroceria
        ) catalogs ORDER BY catalog
        """,
    ),
    Query(
        "vehicle_relationships",
        """
        SELECT relation, reference_count, valid, orphaned,
               ROUND(100.0 * valid / NULLIF(reference_count, 0), 2) valid_pct
        FROM (
            SELECT 'owner' relation,
                   COUNT(*) FILTER (WHERE v.idpropietario IS NOT NULL) reference_count,
                   COUNT(p.idpropietario) valid,
                   COUNT(*) FILTER (WHERE v.idpropietario IS NOT NULL AND p.idpropietario IS NULL) orphaned
            FROM public.vehiculo v LEFT JOIN public.propietario p ON p.idpropietario = v.idpropietario
            UNION ALL
            SELECT 'class', COUNT(*) FILTER (WHERE v.idclase IS NOT NULL), COUNT(c.idclase),
                   COUNT(*) FILTER (WHERE v.idclase IS NOT NULL AND c.idclase IS NULL)
            FROM public.vehiculo v LEFT JOIN public.clase c ON c.idclase = v.idclase
            UNION ALL
            SELECT 'brand.public', COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL), COUNT(m.idmarca),
                   COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL AND m.idmarca IS NULL)
            FROM public.vehiculo v LEFT JOIN public.marca m ON m.idmarca = v.idmarca
            UNION ALL
            SELECT 'brand.comercial', COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL), COUNT(m.idmarca),
                   COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL AND m.idmarca IS NULL)
            FROM public.vehiculo v LEFT JOIN comercial.marca m ON m.idmarca = v.idmarca
            UNION ALL
            SELECT 'line.public', COUNT(*) FILTER (WHERE v.idlinea IS NOT NULL AND v.idlinea <> 0), COUNT(l.idlinea),
                   COUNT(*) FILTER (WHERE v.idlinea IS NOT NULL AND v.idlinea <> 0 AND l.idlinea IS NULL)
            FROM public.vehiculo v LEFT JOIN public.lineas l ON l.idlinea = v.idlinea
            UNION ALL
            SELECT 'line.comercial', COUNT(*) FILTER (WHERE v.idlinea IS NOT NULL AND v.idlinea <> 0), COUNT(l.idlinea),
                   COUNT(*) FILTER (WHERE v.idlinea IS NOT NULL AND v.idlinea <> 0 AND l.idlinea IS NULL)
            FROM public.vehiculo v LEFT JOIN comercial.linea l ON l.idlinea = v.idlinea
            UNION ALL
            SELECT 'body_type', COUNT(*) FILTER (WHERE v.idcarroceria IS NOT NULL AND v.idcarroceria <> 0), COUNT(c.idcarroceria),
                   COUNT(*) FILTER (WHERE v.idcarroceria IS NOT NULL AND v.idcarroceria <> 0 AND c.idcarroceria IS NULL)
            FROM public.vehiculo v LEFT JOIN transportes.vehiculo_carroceria c ON c.idcarroceria = v.idcarroceria
            UNION ALL
            SELECT 'branch_fin', COUNT(*) FILTER (WHERE v.idsucursal_fin IS NOT NULL), COUNT(s.idsucursal),
                   COUNT(*) FILTER (WHERE v.idsucursal_fin IS NOT NULL AND s.idsucursal IS NULL)
            FROM public.vehiculo v LEFT JOIN public.sucursal s ON s.idsucursal = v.idsucursal_fin
        ) integrity ORDER BY relation
        """,
    ),
    Query(
        "owner_cardinality",
        """
        WITH counts AS (
            SELECT idpropietario, COUNT(*) vehicle_count
            FROM public.vehiculo
            WHERE idpropietario IS NOT NULL
            GROUP BY idpropietario
        )
        SELECT COUNT(*) owners_referenced,
               COUNT(*) FILTER (WHERE vehicle_count = 1) owners_with_one_vehicle,
               COUNT(*) FILTER (WHERE vehicle_count > 1) owners_with_many_vehicles,
               COALESCE(MAX(vehicle_count), 0) max_vehicles_per_owner,
               ROUND(COALESCE(AVG(vehicle_count), 0), 2) avg_vehicles_per_owner
        FROM counts
        """,
    ),
    Query(
        "driver_evidence",
        """
        SELECT source, reference_count, matches FROM (
            SELECT 'manifest.transportista' source,
                   COUNT(*) FILTER (WHERE m.idconductor IS NOT NULL) reference_count,
                   COUNT(t.idtransportista) matches
            FROM transportes.manifiesto m LEFT JOIN public.transportista t ON t.idtransportista = m.idconductor
            UNION ALL
            SELECT 'manifest.personal', COUNT(*) FILTER (WHERE m.idconductor IS NOT NULL), COUNT(p.idpersonal)
            FROM transportes.manifiesto m LEFT JOIN public.personal p ON p.idpersonal = m.idconductor
            UNION ALL
            SELECT 'vehicle_driver.transportista', COUNT(*) FILTER (WHERE vc.idchofer IS NOT NULL), COUNT(t.idtransportista)
            FROM public.vehiculochoferes vc LEFT JOIN public.transportista t ON t.idtransportista = vc.idchofer
            UNION ALL
            SELECT 'vehicle_driver.personal', COUNT(*) FILTER (WHERE vc.idchofer IS NOT NULL), COUNT(p.idpersonal)
            FROM public.vehiculochoferes vc LEFT JOIN public.personal p ON p.idpersonal = vc.idchofer
            UNION ALL
            SELECT 'papeleta.transportista', COUNT(*) FILTER (WHERE pa.idinfractor IS NOT NULL), COUNT(t.idtransportista)
            FROM administrativo.papeleta pa LEFT JOIN public.transportista t ON t.idtransportista = pa.idinfractor
            UNION ALL
            SELECT 'papeleta.personal', COUNT(*) FILTER (WHERE pa.idinfractor IS NOT NULL), COUNT(p.idpersonal)
            FROM administrativo.papeleta pa LEFT JOIN public.personal p ON p.idpersonal = pa.idinfractor
        ) evidence ORDER BY source
        """,
    ),
    Query(
        "route_summary",
        """
        WITH pairs AS (
            SELECT idorigen, iddestino, COUNT(*) quantity
            FROM public.recorridos GROUP BY idorigen, iddestino
        )
        SELECT (SELECT COUNT(*) FROM public.recorridos) total,
               (SELECT COUNT(DISTINCT idrecorrido) FROM public.recorridos) distinct_pk,
               (SELECT COUNT(*) FROM public.recorridos WHERE idorigen IS NULL) null_origin,
               (SELECT COUNT(*) FROM public.recorridos WHERE iddestino IS NULL) null_destination,
               (SELECT COUNT(*) FROM pairs WHERE quantity > 1) duplicated_origin_destination_pairs,
               (SELECT COUNT(*) FROM transportes.manifiesto WHERE idrecorrido IS NOT NULL) manifest_references,
               (SELECT COUNT(*) FROM transportes.manifiesto m JOIN public.recorridos r ON r.idrecorrido = m.idrecorrido) manifest_matches
        """,
    ),
    Query(
        "vehicle_documents",
        """
        SELECT 'vehicle' entity,
               COUNT(*) total,
               COUNT(*) FILTER (WHERE soatfechaexpedicion IS NOT NULL) soat_issued,
               COUNT(*) FILTER (WHERE soatfechacaducacion IS NOT NULL) soat_expires,
               COUNT(*) FILTER (WHERE revisionfechaexpedicion IS NOT NULL) inspection_issued,
               COUNT(*) FILTER (WHERE revisionfechacaducacion IS NOT NULL) inspection_expires,
               COUNT(*) FILTER (WHERE fechavencpermisos IS NOT NULL) permits_expire,
               COUNT(*) FILTER (WHERE feccontratocaducacion IS NOT NULL) contract_expires,
               0 license_expires
        FROM public.vehiculo
        UNION ALL
        SELECT 'transportista', COUNT(*), 0, 0, 0, 0, 0, 0,
               COUNT(*) FILTER (WHERE fecvencimiento IS NOT NULL)
        FROM public.transportista
        UNION ALL
        SELECT 'vehicle_permission', COUNT(*), 0, 0, 0, 0,
               COUNT(*) FILTER (WHERE fechavencpermisos IS NOT NULL), 0, 0
        FROM transportes.vehiculo_permisos
        """,
    ),
    Query(
        "manifest_summary",
        """
        SELECT COUNT(*) total,
               COUNT(DISTINCT idmanifiesto) distinct_pk,
               COUNT(*) FILTER (WHERE idmanifiesto IS NULL) null_pk,
               MIN(documentofecha) min_document_date,
               MAX(documentofecha) max_document_date,
               MIN(fecha_viaje) min_trip_date,
               MAX(fecha_viaje) max_trip_date,
               COUNT(*) FILTER (WHERE idvehiculo IS NOT NULL) vehicle_references,
               COUNT(v.idvehiculo) vehicle_matches,
               COUNT(*) FILTER (WHERE idrecorrido IS NOT NULL) route_references,
               COUNT(r.idrecorrido) route_matches,
               COUNT(*) FILTER (WHERE idconductor IS NOT NULL) driver_references,
               COUNT(t.idtransportista) transportista_matches,
               COUNT(*) FILTER (WHERE documentoserie IS NOT NULL OR documentonumero IS NOT NULL) numbered
        FROM transportes.manifiesto m
        LEFT JOIN public.vehiculo v ON v.idvehiculo = m.idvehiculo
        LEFT JOIN public.recorridos r ON r.idrecorrido = m.idrecorrido
        LEFT JOIN public.transportista t ON t.idtransportista = m.idconductor
        """,
    ),
    Query(
        "manifest_state_column",
        """
        SELECT COUNT(*) AS state_column_count
        FROM information_schema.columns
        WHERE table_schema = 'transportes' AND table_name = 'manifiesto' AND column_name = 'estado'
        """,
    ),
    Query(
        "papeleta_matrix",
        """
        SELECT COALESCE(estado::text, '<NULL>') estado,
               COALESCE(estadopago::text, '<NULL>') estadopago,
               COUNT(*) cantidad
        FROM administrativo.papeleta
        GROUP BY estado, estadopago
        ORDER BY estado, estadopago
        """,
    ),
    Query(
        "papeleta_relationships",
        """
        SELECT relation, reference_count, matches FROM (
            SELECT 'vehicle' relation, COUNT(*) FILTER (WHERE p.idvehiculo IS NOT NULL) reference_count, COUNT(v.idvehiculo) matches
            FROM administrativo.papeleta p LEFT JOIN public.vehiculo v ON v.idvehiculo = p.idvehiculo
            UNION ALL
            SELECT 'infractor.transportista', COUNT(*) FILTER (WHERE p.idinfractor IS NOT NULL), COUNT(t.idtransportista)
            FROM administrativo.papeleta p LEFT JOIN public.transportista t ON t.idtransportista = p.idinfractor
            UNION ALL
            SELECT 'infractor.personal', COUNT(*) FILTER (WHERE p.idinfractor IS NOT NULL), COUNT(pe.idpersonal)
            FROM administrativo.papeleta p LEFT JOIN public.personal pe ON pe.idpersonal = p.idinfractor
        ) relations ORDER BY relation
        """,
    ),
    Query(
        "d6_schemas",
        """
        SELECT requested.schema_name,
               CASE WHEN actual.schema_name IS NULL THEN false ELSE true END is_present
        FROM (VALUES ('reglasnegocio'), ('logistica'), ('caja')) requested(schema_name)
        LEFT JOIN information_schema.schemata actual USING (schema_name)
        ORDER BY requested.schema_name
        """,
    ),
    Query(
        "d6_foreign_servers",
        """
        SELECT foreign_server_name, foreign_data_wrapper_name
        FROM information_schema.foreign_servers
        ORDER BY foreign_server_name
        """,
    ),
    Query(
        "d6_extensions",
        """
        SELECT extname FROM pg_extension
        WHERE extname IN ('dblink', 'postgres_fdw')
        ORDER BY extname
        """,
    ),
    Query(
        "d6_routines",
        """
        SELECT routine_schema, routine_name
        FROM information_schema.routines
        WHERE routine_definition ILIKE ANY (ARRAY['%reglasnegocio%', '%logistica.%', '%caja.%'])
        ORDER BY routine_schema, routine_name
        """,
    ),
)


OPTIONAL_QUERIES = {
    ("transportes", "vehiculo_modelo"): Query(
        "vehicle_model_catalog_match",
        """
        WITH vehicle_models AS (
            SELECT DISTINCT LOWER(BTRIM(modelo)) value
            FROM public.vehiculo
            WHERE modelo IS NOT NULL AND BTRIM(modelo) <> ''
        ), catalog_models AS (
            SELECT DISTINCT LOWER(BTRIM(descripcion)) value
            FROM transportes.vehiculo_modelo
            WHERE descripcion IS NOT NULL AND BTRIM(descripcion) <> ''
        )
        SELECT (SELECT COUNT(*) FROM vehicle_models) vehicle_distinct_models,
               (SELECT COUNT(*) FROM catalog_models) catalog_distinct_models,
               (SELECT COUNT(*) FROM vehicle_models v JOIN catalog_models c USING (value)) matched_distinct_models
        """,
    )
}


def validate_queries() -> None:
    for query in (*QUERIES, *OPTIONAL_QUERIES.values()):
        sql = query.sql.strip()
        if not ALLOWED_START.match(sql):
            raise ValueError(f"Query no permitida: {query.name}")
        if FORBIDDEN_SQL.search(sql):
            raise ValueError(f"Palabra SQL prohibida en: {query.name}")
        if EXPLICIT_PII_COLUMN.search(sql):
            raise ValueError(f"Columna PII prohibida en: {query.name}")
        if SELECT_ALL.search(sql):
            raise ValueError(f"SELECT * prohibido en: {query.name}")
        if ";" in sql.rstrip(";"):
            raise ValueError(f"Solo se permite una sentencia por query: {query.name}")


def json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    return value


def rows_as_dicts(cursor: Any) -> list[dict[str, Any]]:
    columns = [item.name if hasattr(item, "name") else item[0] for item in cursor.description]
    return [{column: json_value(value) for column, value in zip(columns, row)} for row in cursor.fetchall()]


def connection_parameters() -> tuple[str | None, dict[str, str]]:
    dsn = os.getenv("FLEET_AUDIT_DSN")
    if dsn:
        return dsn, {}
    names = {
        "host": "FLEET_AUDIT_HOST",
        "port": "FLEET_AUDIT_PORT",
        "dbname": "FLEET_AUDIT_DATABASE",
        "user": "FLEET_AUDIT_USER",
        "password": "FLEET_AUDIT_PASSWORD",
        "sslmode": "FLEET_AUDIT_SSLMODE",
    }
    params = {key: os.environ[env] for key, env in names.items() if os.getenv(env)}
    required = {"host", "dbname", "user", "password"}
    if not required.issubset(params):
        raise RuntimeError("missing_connection_environment")
    params.setdefault("port", "5432")
    params.setdefault("sslmode", "require")
    return None, params


def verify_read_only(cursor: Any) -> dict[str, Any]:
    cursor.execute("SHOW transaction_read_only")
    transaction_read_only = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT COALESCE((SELECT usesuper FROM pg_user WHERE usename = current_user), false) AS superuser,
               COUNT(*) FILTER (WHERE has_table_privilege(current_user, quote_ident(table_schema) || '.' || quote_ident(table_name), 'INSERT')) AS insert_tables,
               COUNT(*) FILTER (WHERE has_table_privilege(current_user, quote_ident(table_schema) || '.' || quote_ident(table_name), 'UPDATE')) AS update_tables,
               COUNT(*) FILTER (WHERE has_table_privilege(current_user, quote_ident(table_schema) || '.' || quote_ident(table_name), 'DELETE')) AS delete_tables,
               COUNT(*) FILTER (WHERE has_table_privilege(current_user, quote_ident(table_schema) || '.' || quote_ident(table_name), 'TRUNCATE')) AS truncate_tables,
               (SELECT COUNT(*)
                  FROM (VALUES ('public'), ('comercial'), ('transportes'), ('administrativo')) AS audited(schema_name)
                 WHERE has_schema_privilege(current_user, audited.schema_name, 'CREATE')) AS create_schemas,
               has_database_privilege(current_user, current_database(), 'CREATE') AS create_database_objects
        FROM information_schema.tables
        WHERE table_schema IN ('public', 'administrativo', 'transportes', 'comercial')
        """
    )
    superuser, inserts, updates, deletes, truncates, create_schemas, create_database_objects = cursor.fetchone()
    if str(transaction_read_only).lower() not in {"on", "true"}:
        raise RuntimeError("transaction_not_read_only")
    if superuser or inserts or updates or deletes or truncates or create_schemas or create_database_objects:
        raise RuntimeError("account_has_write_privileges")
    return {
        "transaction_read_only": True,
        "superuser": False,
        "insert_privileged_tables": 0,
        "update_privileged_tables": 0,
        "delete_privileged_tables": 0,
        "truncate_privileged_tables": 0,
        "create_privileged_schemas": 0,
        "create_database_objects": False,
    }


def run_profile(timeout_ms: int) -> dict[str, Any]:
    expected_database = os.getenv("FLEET_AUDIT_EXPECTED_DATABASE")
    if not expected_database:
        raise RuntimeError("missing_expected_database")
    try:
        import psycopg  # type: ignore
    except ImportError as exc:
        raise RuntimeError("psycopg_not_installed") from exc

    dsn, params = connection_parameters()
    connect_args: tuple[Any, ...] = (dsn,) if dsn else ()
    connection = psycopg.connect(*connect_args, **params, autocommit=True)
    try:
        with connection.cursor() as cursor:
            cursor.execute(BEGIN_READ_ONLY_SQL)
            try:
                cursor.execute(
                    TIMEOUT_SQL,
                    (f"{timeout_ms}ms",),
                )
                guard = verify_read_only(cursor)
                cursor.execute(METADATA_SQL)
                metadata = rows_as_dicts(cursor)[0]
                if metadata["database"] != expected_database:
                    raise RuntimeError("unexpected_database")
                results: dict[str, Any] = {}
                for query in QUERIES:
                    try:
                        cursor.execute(query.sql)
                    except Exception as exc:
                        raise RuntimeError(f"query_failed:{query.name}") from exc
                    results[query.name] = rows_as_dicts(cursor)
                inventory = {
                    (row["table_schema"], row["table_name"])
                    for row in results["catalog_inventory"]
                }
                for object_name, query in OPTIONAL_QUERIES.items():
                    if object_name in inventory:
                        try:
                            cursor.execute(query.sql)
                        except Exception as exc:
                            raise RuntimeError(f"query_failed:{query.name}") from exc
                        results[query.name] = rows_as_dicts(cursor)
                return {"metadata": metadata, "read_only_guard": guard, "results": results}
            finally:
                cursor.execute(ROLLBACK_SQL)
    finally:
        connection.close()


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Fleet production profile",
        "",
        f"- Base verificada: `{report['metadata']['database']}`",
        f"- Fecha: `{report['metadata']['execution_date']}`",
        "- Transacción read-only: `true`",
        "- Privilegios DML detectados: `0`",
    ]
    for name, rows in report["results"].items():
        lines.extend(["", f"## {name}", ""])
        if not rows:
            lines.append("Sin filas.")
            continue
        columns = list(rows[0])
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("|" + "|".join("---" for _ in columns) + "|")
        for row in rows:
            values = [str(row[column]).replace("|", "\\|") for column in columns]
            lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def self_test() -> None:
    validate_queries()
    if BEGIN_READ_ONLY_SQL != "BEGIN READ ONLY":
        raise RuntimeError("self_test_missing_read_only_transaction")
    if ROLLBACK_SQL != "ROLLBACK":
        raise RuntimeError("self_test_missing_rollback")
    if not ALLOWED_START.match(TIMEOUT_SQL) or "statement_timeout" not in TIMEOUT_SQL:
        raise RuntimeError("self_test_missing_timeout")
    if not ALLOWED_START.match(METADATA_SQL):
        raise RuntimeError("self_test_invalid_metadata_query")
    sample = {
        "metadata": {"database": "AUTHORIZED_DATABASE", "execution_date": "2000-01-01"},
        "read_only_guard": {"transaction_read_only": True},
        "results": {"sample_aggregate": [{"total": 3, "nulls": 1}]},
    }
    rendered_json = json.dumps(sample, default=json_value)
    rendered_markdown = markdown_report(sample)
    forbidden_output = re.compile(r"password|token|dsn=|postgres(?:ql)?://", re.IGNORECASE)
    if forbidden_output.search(rendered_json + rendered_markdown):
        raise RuntimeError("self_test_sensitive_output")
    print(
        "SELF-TEST OK: sin DML/DDL/PII/SELECT *, "
        "BEGIN READ ONLY, timeout, ROLLBACK y salida agregada validados"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=60_000)
    args = parser.parse_args()

    if not 1_000 <= args.timeout_ms <= 300_000:
        parser.error("--timeout-ms debe estar entre 1000 y 300000")

    try:
        validate_queries()
        if args.self_test:
            self_test()
            return 0
        report = run_profile(args.timeout_ms)
        output = (
            json.dumps(report, indent=2, ensure_ascii=False, default=json_value) + "\n"
            if args.format == "json"
            else markdown_report(report)
        )
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except RuntimeError as exc:
        # Solo se imprime un código controlado; nunca el error del driver o el DSN.
        print(f"AUDIT_ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("AUDIT_ERROR: unexpected_failure", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

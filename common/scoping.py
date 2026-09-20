from django.db.models import Q
from rest_framework.exceptions import PermissionDenied


def scope_values(user):
    roles = user.roles.filter(is_active=True, profile__is_active=True)
    company_ids = set(roles.values_list("company_id", flat=True))
    global_company_ids = set(roles.filter(branch__isnull=True).values_list("company_id", flat=True))
    branch_ids = set(roles.filter(branch__isnull=False).values_list("branch_id", flat=True))
    return company_ids, global_company_ids, branch_ids


def can_access_company(user, company_id):
    if user.is_superuser:
        return True
    company_ids, _, _ = scope_values(user)
    return int(company_id) in company_ids


def can_access_branch(user, branch_id):
    if user.is_superuser:
        return True
    from apps.core.models import Sucursal
    _, global_company_ids, branch_ids = scope_values(user)
    if int(branch_id) in branch_ids:
        return True
    return Sucursal.objects.filter(pk=branch_id, empresa_id__in=global_company_ids).exists()


def require_branch_access(user, branch_id):
    if not can_access_branch(user, branch_id):
        raise PermissionDenied("La sucursal está fuera del ámbito autorizado.")


def scope_queryset(queryset, user, *, branch_lookup=None, company_lookup=None):
    if user.is_superuser:
        return queryset
    company_ids, global_company_ids, branch_ids = scope_values(user)
    if branch_lookup is not None:
        if branch_lookup:
            condition = Q(**{f"{branch_lookup}__empresa_id__in": global_company_ids}) | Q(
                **{f"{branch_lookup}__id__in": branch_ids}
            )
        else:
            condition = Q(empresa_id__in=global_company_ids) | Q(pk__in=branch_ids)
        return queryset.filter(condition).distinct()
    if company_lookup is not None:
        lookup = f"{company_lookup}__id__in" if company_lookup else "pk__in"
        return queryset.filter(**{lookup: company_ids}).distinct()
    return queryset


class ScopedQuerysetMixin:
    scope_branch_lookup = None
    scope_company_lookup = None

    def get_queryset(self):
        return scope_queryset(
            super().get_queryset(), self.request.user,
            branch_lookup=self.scope_branch_lookup, company_lookup=self.scope_company_lookup,
        )

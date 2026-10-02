import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("attendance", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="attendanceevent",
            name="direction",
            field=models.CharField(
                choices=[("entry", "Entrada"), ("exit", "Salida"), ("unknown", "Sin determinar")],
                db_index=True,
                default="unknown",
                max_length=12,
            ),
        ),
        migrations.CreateModel(
            name="DeviceCommand",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("command", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("sent", "Enviado"),
                            ("acknowledged", "Confirmado"),
                            ("failed", "Fallido"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("response", models.TextField(blank=True)),
                (
                    "device",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="commands", to="attendance.attendancedevice"),
                ),
            ],
            options={"indexes": [models.Index(fields=["device", "status", "created_at"], name="att_cmd_dev_stat_created_idx")]},
        ),
    ]

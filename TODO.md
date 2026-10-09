# TODO.md

## ETL - Pendientes (no bloqueantes)

### Media prioridad
- [ ] Dockerfile para despliegue
- [ ] README.md con diagrama y quickstart
- [ ] CI con GitHub Actions
- [ ] `--taxi` argument en argparse

### Baja prioridad
- [ ] Pandera para validación de datos
- [ ] Métricas de tiempos por etapa
- [ ] Pre-commit hooks (ruff, black, mypy)
- [ ] Alertas Slack/email

### Descartado (por ahora)
- Delta Lake / Iceberg (Parquet plano es suficiente)
- Airflow / Prefect (overkill para 4 archivos)
- Kubernetes (VPS no lo necesita)
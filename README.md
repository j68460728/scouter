# Scouter Engine

Scouter Engine es un sistema de análisis deportivo autónomo, reproducible y auditable, diseñado para identificar enfrentamientos con una diferencia competitiva significativa en el fútbol profesional utilizando datos reales.

## Arquitectura
El sistema separa claramente la lógica de ejecución de la configuración de datos para facilitar el mantenimiento y la reutilización:

- `bin/`: Contiene el ejecutable principal (`scout`).
- `config/`: Configuración de ligas y fuentes de datos.
- `instructions/`: Define el flujo de trabajo obligatorio.
- `rules/`: Contiene la matriz de puntuación (definida en YAML).
- `src/`: Lógica central (scraper, evaluador, reportero).
- `templates/`: Plantillas para la generación de informes (Jinja2).
- `evidence/`, `reports/`, `logs/`: Directorios de salida para la trazabilidad de cada ejecución.

## Uso
Para ejecutar el análisis, asegúrese de estar en el directorio raíz del proyecto y utilice el siguiente comando:

```bash
./bin/scout analyze --mode [rules|ai]
```

Este comando inicia un flujo de trabajo autónomo donde el agente:
1. Calcula la ventana temporal de las próximas 24 horas.
2. Descarga datos reales desde fuentes oficiales (football-data.co.uk).
3. Aplica la matriz de puntuación objetiva definida en `rules/scoring_matrix.yaml`.
4. Descarta partidos que no cumplen el umbral definido.
5. Genera el informe final con justificación técnica.

## Guía de Usuario
Consulte `docs/USER_GUIDE.md` para entender cómo interpretar los informes generados y cómo ajustar los criterios de análisis.

## Qué esperar
Tras la ejecución, el sistema generará los siguientes artefactos en sus respectivos directorios:
- **Informe Final (`reports/`):** Archivo Markdown con el desglose técnico, justificación y puntuación.
- **Evidencia (`evidence/`):** Datos crudos procesados que sustentan el análisis.
- **Auditoría (`logs/`):** Registro detallado de la ejecución.

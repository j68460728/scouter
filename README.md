# Scouter Engine

Scouter Engine es un sistema de análisis deportivo autónomo, reproducible y auditable, diseñado para identificar enfrentamientos con una diferencia competitiva significativa en el fútbol profesional.

El proyecto está diseñado para funcionar como un motor independiente que procesa información basándose en reglas de negocio estrictas, eliminando la ambigüedad y garantizando la trazabilidad total de los resultados.

## Arquitectura

El sistema separa claramente la lógica de ejecución de la configuración de datos para facilitar el mantenimiento y la reutilización:

- `bin/`: Contiene el ejecutable principal (`scout`).
- `instructions/`: Define el flujo de trabajo obligatorio.
- `rules/`: Contiene la matriz de puntuación (definida en YAML).
- `sources/`: Registro de fuentes oficiales y protocolos de resolución de conflictos.
- `templates/`: Plantillas para la generación de informes (Jinja2).
- `evidence/`, `reports/`, `logs/`: Directorios de salida para la trazabilidad de cada ejecución.

## Uso

Para ejecutar el análisis, asegúrese de estar en el directorio raíz del proyecto y utilice el siguiente comando:

```bash
./bin/scout analyze
```

Este comando inicia un flujo de trabajo autónomo donde el agente:
1. Calcula la ventana temporal de las próximas 24 horas.
2. Descubre los encuentros en las fuentes configuradas.
3. Aplica la matriz de puntuación objetiva.
4. Descarta partidos que no cumplen el umbral definido (>= 8).
5. Genera el informe final con justificación técnica y cita de fuentes.

## Qué esperar

Tras la ejecución, el sistema generará los siguientes artefactos en sus respectivos directorios:

- **Informe Final (`reports/`):** Un archivo en formato Markdown con el desglose técnico, justificación y puntuación de los partidos seleccionados.
- **Evidencia (`evidence/`):** Datos crudos obtenidos de las fuentes que sustentan el análisis.
- **Auditoría (`logs/`):** Registro detallado de la ejecución, incluyendo fuentes consultadas, inconsistencias detectadas y motivos de descarte de partidos.

Cada ejecución es independiente y almacena toda la trazabilidad necesaria para reconstruir el proceso posteriormente.

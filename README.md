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

### Ejecución Local (Recomendada)

Para ejecutar el análisis sin Docker (modo local):

```bash
./bin/scout analyze --mode rules   # Análisis basado en reglas
./bin/scout analyze --mode ai      # Análisis con IA (fallback a reglas si no hay servicio IA)
```

El script detecta automáticamente si Docker está disponible y, si no lo está, ejecuta en modo local.

### Ejecución con Docker

Si tienes Docker instalado y configurado:

```bash
./bin/scout analyze --mode rules
./bin/scout analyze --mode ai
```

O forzar modo local explícitamente:

```bash
./bin/scout analyze --mode ai --no-docker
```

### Configuración del Servicio de IA (Opcional)

Para habilitar el modo AI con un proveedor de LLM externo, configura las siguientes variables de entorno:

```bash
export API_BASE_URL="http://localhost:20128/v1"  # URL del servicio de IA
export AI_MODEL="google/gemini-pro"              # Modelo a utilizar
export AI_TIMEOUT="60"                           # Timeout en segundos
```

Si el servicio de IA no está disponible, el sistema utiliza automáticamente un **fallback basado en reglas** para garantizar que siempre se genere un reporte útil.

## Flujo de Trabajo

El sistema ejecuta las siguientes etapas:

1. **Recolección**: Obtiene partidos de las fuentes configuradas (actualmente datos de ejemplo).
2. **Evaluación**: 
   - Modo `rules`: Aplica la matriz de puntuación definida en `rules/scoring_matrix.yaml`.
   - Modo `ai`: Consulta un modelo de lenguaje para evaluación contextual (con fallback a reglas).
3. **Reporte**: Genera informe Markdown con justificación técnica y evidencia JSON.

## Qué esperar

Tras la ejecución, el sistema generará los siguientes artefactos en sus respectivos directorios:

- **Informe Final (`reports/`):** Un archivo en formato Markdown con el desglose técnico, justificación y puntuación de los partidos seleccionados.
- **Evidencia (`evidence/`):** Datos crudos obtenidos de las fuentes que sustentan el análisis.
- **Auditoría (`logs/`):** Registro detallado de la ejecución, incluyendo fuentes consultadas, inconsistencias detectadas y motivos de descarte de partidos.

Cada ejecución es independiente y almacena toda la trazabilidad necesaria para reconstruir el proceso posteriormente.

## Matriz de Puntuación

La matriz actual evalúa los partidos según estos criterios:

| Criterio | Descripción | Puntos Máximos |
|----------|-------------|----------------|
| `category_difference` | Diferencia entre categorías competitivas | 3 |
| `prestige_history` | Títulos nacionales/internacionales, trayectoria histórica | 2 |
| `squad_value` | Valor relativo de la plantilla (verificable) | 2 |
| `ranking_coefficient` | Rankings o coeficientes oficiales | 2 |
| `recent_performance` | Forma reciente verificable | 1 |

**Umbral de selección:** 8 puntos  
**Política de exclusión:** Se descartan partidos con puntuación total < 8.

## Mejoras y Oportunidades Futuras

- [ ] Implementar scraping real de fuentes deportivas (API-Football, ESPN, etc.)
- [ ] Añadir soporte para múltiples proveedores de IA (OpenAI, Anthropic, modelos locales)
- [ ] Integrar validación de datos en tiempo real
- [ ] Añadir tests automatizados
- [ ] Implementar caché de resultados para reducir llamadas externas
- [ ] Añadir interfaz web opcional para visualización de reportes

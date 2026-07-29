# Guía de Usuario: Scouter Engine

Bienvenido a Scouter Engine. Esta guía le ayudará a entender cómo operar el sistema y cómo interpretar los resultados generados.

## 1. Funcionamiento del Sistema
Scouter Engine es una herramienta automatizada que realiza lo siguiente:
1. **Recolección de Datos:** Descarga en tiempo real los datos más recientes de las principales ligas europeas (Premier League, La Liga, Bundesliga, etc.) desde la API oficial de football-data.org.
2. **Evaluación:** Aplica una matriz de puntuación configurable (`rules/scoring_matrix.yaml`) para identificar partidos con alto interés competitivo.
3. **Reporte:** Genera un informe detallado con los partidos seleccionados, su puntuación y la justificación técnica de la selección.

## 2. Modos de Operación
El sistema tiene dos modos de ejecución:
- `rules`: Utiliza una matriz de reglas estricta basada en factores como el nivel de la competición y el prestigio de los equipos. Es totalmente determinista.
- `ai`: (En desarrollo) Utiliza inteligencia artificial para una interpretación más profunda de los datos.

## 3. Parámetros del Comando

```bash
./bin/scout analyze --mode <rules|ai> [--window <valor>]
```

### --mode (obligatorio)
Define el motor de evaluación:
- `rules` → Evaluación por matriz de reglas
- `ai` → Evaluación por IA (en desarrollo)

### --window (opcional)
Filtra partidos dentro de una ventana de tiempo. Acepta:

| Formato | Ejemplo | Significado |
|---|---|---|
| `Nd` | `--window 7d` | Próximos 7 días |
| `Nh` | `--window 48h` | Próximas 48 horas |
| `N` (solo número) | `--window 3` | Próximos 3 días (por defecto) |

**Si se omite `--window`**, se traen **todos** los partidos disponibles de las ligas configuradas.

## 4. Interpretación de Resultados
Al ejecutar `./bin/scout analyze --mode rules`, encontrará un informe en `reports/`.

### Estructura del informe
```
### Arsenal FC vs Coventry City FC
- **Competición:** Premier League
- **Fecha/Hora:** 2026-08-21T19:00:00Z    ← Fecha exacta del encuentro
- **Puntuación:** 10
- **Justificación:**
  - Tier 1 competition (+3)
  - Historical prestige team (+2)
  - High squad value (+2)
  - High ranking coefficient (+2)
  - Verifiable recent form (+1)
```

### ¿Qué significa la puntuación?
Cada partido recibe una puntuación basada en la suma de criterios definidos en `rules/scoring_matrix.yaml` (máximo 10 puntos):
- **Umbral:** Partidos con puntuación >= 8 son seleccionados.
- **Criterios:** Diferencia de categoría (0-3), prestigio histórico (0-2), valor de plantilla (0-2), coeficiente de ranking (0-2), rendimiento reciente (0-1).
- **Justificación:** El informe desglosa cómo se ha alcanzado dicha puntuación.

### Archivos generados
| Archivo | Contenido |
|---|---|
| `reports/report_rules_*.md` | Informe legible con partidos seleccionados |
| `evidence/evidence_rules_*.json` | Datos crudos de evaluación (trazabilidad) |
| `logs/execution_rules_*.log` | Registro de auditoría de la ejecución |

## 5. Solución de Problemas
- **¿No aparecen partidos en el informe?**
  - Pruebe sin `--window` para ver todos los partidos disponibles: `./bin/scout analyze --mode rules`
  - Si ningún partido supera el umbral de 8, intente reducir el threshold en `rules/scoring_matrix.yaml`
- **¿Error 429 (rate limit)?**
  - El sistema espera automáticamente y reintenta. Es normal con la cuenta gratuita (10 req/min).
- **¿Error de conexión?**
  - Verifique su conexión a internet y que `FOOTBALL_DATA_API_KEY` en `docker-compose.yml` sea válida.

## 6. Personalización
Puede ajustar la sensibilidad del análisis modificando `rules/scoring_matrix.yaml`:
```yaml
threshold: 8  # Reduzca para incluir más partidos, aumente para mayor exclusividad
```

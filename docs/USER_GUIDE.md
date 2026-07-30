# Guía de Usuario: Scouter Engine

Bienvenido a Scouter Engine. Esta guía le ayudará a entender cómo operar el sistema y cómo interpretar los resultados generados.

## 1. Funcionamiento del Sistema
Scouter Engine es una herramienta automatizada que realiza lo siguiente:
1. **Recolección de Datos:** Descarga en tiempo real datos de ligas (matches, standings, resultados históricos) desde la API oficial de football-data.org.
2. **Evaluación:** Construye un perfil de fuerza (0–100) para cada equipo basado en:
   - **Estructural** (60%): coeficiente de competición, puntos por partido, diferencia de goles de temporada
   - **Forma reciente** (30%): Goal Superiority Rating (GSR), PPG y promedio de goles en últimos N partidos
   - **Contexto** (10%): ventaja de localía, fase de la competición
3. **Reporte:** Genera un informe con la diferencia de fuerza entre equipos y selecciona los partidos más desiguales.

## 2. Modos de Operación
El sistema tiene dos modos de ejecución:
- `rules`: **Motor determinista de fuerza**. Compara equipos mediante datos objetivos. Es el modo recomendado.
- `ai`: (Experimental) Utiliza inteligencia artificial. Independiente del motor de fuerza.

## 3. Parámetros del Comando

```bash
./bin/scout analyze --mode <rules|ai> [--window <valor>]
```

### --mode (obligatorio)
Define el motor de evaluación:
- `rules` → Evaluación por diferencia de fuerza (Team Strength 0–100)
- `ai` → Evaluación por IA (experimental)

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
### ⭐ Manchester City FC (Favorito) vs AFC Bournemouth — Diferencia: 15.0 pts
- **Competición:** Premier League
- **Fecha/Hora (Colombia):** 2026-08-23 08:00     ← Hora local Colombia (UTC-5)
- **Fuerza local (Manchester City FC):** 54.1/100
  - Estructural: 48.1/60
  - Forma reciente: 0.0/30                          ← GSR si hay datos suficientes
  - Contexto: 6.0/10
- **Fuerza visitante (AFC Bournemouth):** 39.1/100
  - Estructural: 38.1/60
  - Forma reciente: 0.0/30
  - Contexto: 1.0/10
```

### ⭐ Indicador de Favorito
El equipo con mayor `total/100` es marcado como favorito. La determinación es completamente objetiva:
- No hay listas de equipos "prestigiosos" hardcodeadas
- El favorito es quien tenga mejor rating compuesto (estructural + forma reciente + contexto)
- La ventaja de localía aporta hasta 5 puntos dentro del componente de contexto

### ¿Qué significa la fuerza (0–100)?
El rating es la suma ponderada de tres pilares:
| Pilar | Peso | Componentes |
|---|---|---|
| **Estructural** | 60% | Coeficiente de competición (0–25), PPG en liga (0–25), DG de temporada (0–10) |
| **Forma reciente** | 30% | GSR últimos 6 partidos (0–15), PPG últimos 6 (0–10), promedio de goles (0–5) |
| **Contexto** | 10% | Ventaja local (0–5), fase de competición (0–5) |

### Criterio de selección
Se seleccionan partidos donde `abs(fuerza_local - fuerza_visitante) >= 15` puntos. Esto garantiza que solo se reporten encuentros con diferencia significativa.

### Archivos generados
| Archivo | Contenido |
|---|---|
| `reports/report_rules_*.md` | Informe legible con partidos seleccionados y desglose de fuerza |
| `evidence/evidence_rules_*.json` | Datos crudos de evaluación (trazabilidad) |
| `logs/execution_rules_*.log` | Registro de auditoría de la ejecución |

## 5. Solución de Problemas
- **¿No aparecen partidos en el informe?**
  - Pruebe sin `--window`: `./bin/scout analyze --mode rules`
  - Si sigue sin resultados, reduzca `confidence.min_difference` en `rules/strength_matrix.yaml`
  - La forma reciente puede mostrar 0.0 si la temporada no ha iniciado (no hay datos de GSR suficientes)
- **¿Error 429 (rate limit)?**
  - El sistema espera automáticamente y reintenta. Es normal con la cuenta gratuita (10 req/min).
- **¿Error de conexión?**
  - Verifique su conexión a internet y que `FOOTBALL_DATA_API_KEY` en `docker-compose.yml` sea válida.

## 6. Personalización
Puede ajustar el comportamiento editando `rules/strength_matrix.yaml`:
```yaml
confidence:
  min_difference: 15     # Reduzca para incluir más partidos, aumente para mayor exclusividad
weights:
  structural: 0.60       # Peso de fuerza estructural
  recent_form: 0.30      # Peso de forma reciente (incluye GSR)
  context: 0.10          # Peso de contexto (localía, fase)
gsr:
  matches: 6             # Partidos para calcular GSR
  min_matches: 5         # Mínimo para que GSR sea válido
```

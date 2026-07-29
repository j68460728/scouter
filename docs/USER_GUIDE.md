# Guía de Usuario: Scouter Engine

Bienvenido a Scouter Engine. Esta guía le ayudará a entender cómo operar el sistema y cómo interpretar los resultados generados.

## 1. Funcionamiento del Sistema
Scouter Engine es una herramienta automatizada que realiza lo siguiente:
1. **Recolección de Datos:** Descarga en tiempo real los datos más recientes de las principales ligas europeas (Premier League, La Liga, Bundesliga, etc.) desde fuentes oficiales.
2. **Evaluación:** Aplica una matriz de puntuación configurable (`rules/scoring_matrix.yaml`) para identificar partidos con alto interés competitivo.
3. **Reporte:** Genera un informe detallado con los partidos seleccionados, su puntuación y la justificación técnica de la selección.

## 2. Modos de Operación
El sistema tiene dos modos principales de ejecución:
- `rules`: Utiliza una matriz de reglas estricta basada en factores como el nivel de la competición y la categoría de los equipos. Es totalmente determinista.
- `ai`: (En desarrollo) Utiliza inteligencia artificial para una interpretación más profunda de los datos.

## 3. Interpretación de Resultados
Al ejecutar `./bin/scout analyze --mode rules`, encontrará un informe en `reports/`.

### ¿Qué significa la puntuación?
Cada partido recibe una puntuación basada en la suma de criterios definidos en `rules/scoring_matrix.yaml`.
- **Umbral:** Actualmente, los partidos con una puntuación >= 8 son seleccionados para el informe final.
- **Justificación:** El informe desglosa cómo se ha alcanzado dicha puntuación (ej. nivel de competición, prestigio histórico del equipo).

### Solución de Problemas
- **¿No aparecen partidos en el informe?** 
  Es posible que no haya partidos programados en las próximas 24 horas en las ligas configuradas o que ningún partido alcance el umbral de puntuación necesario.
- **¿Error de conexión?**
  Verifique que tiene acceso a internet y que la clave de API configurada en `docker-compose.yml` (`FOOTBALL_DATA_API_KEY`) es válida.

## 4. Personalización
Puede ajustar la agresividad del filtro de selección modificando el parámetro `threshold` en `rules/scoring_matrix.yaml`. Un umbral más alto filtrará partidos de mayor calidad competitiva, mientras que un umbral más bajo incluirá más eventos.

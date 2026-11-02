# Rendimiento

**Meta:** cada pantalla responde en menos de **2 segundos** (percentil 95) en un colegio de tamaño real.

## Cómo se mide

1. Colegio grande de prueba: unas 560 matrículas en 20 aulas, con tres bimestres de notas, asistencia diaria, conducta y encuesta familiar.
2. Se evalúa el riesgo de todo el colegio.
3. Cada pantalla principal se pide 20 veces con el rol que la usa (más una petición de calentamiento que no cuenta), y se calculan p50, p95 y máximo.

```bash
docker compose exec api python -m scripts.seed_dev --size large
python -m scripts.measure_performance        # desde services/api, con el entorno virtual
```

El script termina con error si alguna pantalla supera la meta.

## Protección contra consultas N+1

`tests/test_query_counts.py` cuenta las sentencias SQL de las listas más usadas (resumen del director, estudiantes de un aula, recomendaciones y alertas) con pocos estudiantes y con muchos. El número debe ser el mismo: si alguien agrega una consulta por estudiante, el test falla.

Para lograrlo, las listas cargan por adelantado lo que su respuesta necesita (aula, evaluación y apoderados de cada estudiante), en lugar de consultarlo fila por fila.

## Resultados

| Pantalla | p50 | p95 |
|---|---|---|
| _Completar con la salida de `measure_performance` en la máquina de referencia._ | | |

Máquina de referencia: Lenovo V15 G4 (Ryzen 3 7320U, 8 GB de RAM), Docker Desktop con 4 GB, MySQL 8.

# AB-GEN — Investigación de Visión Geométrica / Espectral / Polinómica

> **Investigación experimental de clasificación de imágenes con una política de reproducibilidad basada en evidencia**

AB-GEN es una arquitectura experimental de visión artificial basada en reducción dimensional, ponderación Fisher, características espectrales multiescala, estructura geométrica de clases, un ensemble N1 y un meta-aprendiz N2.

**Sitio oficial de investigación:** https://msrobotikaabgenresearch.wordpress.com

## Estado actual de la evidencia

| Ruta | Resultado | Estado | Interpretación |
|---|---:|---|---|
| V24 Slow Burn histórico | **80,14 %** | **REPORTADO** | Registro histórico; la reproducción exacta RAW→PCA→modelo no está establecida. |
| Elite / Slow Burn recuperado | **80,17 %** | **RECUPERADO** | Ejecución desde caché PCA; no demuestra la ruta histórica exacta del 80,14 %. |
| M5 MASTER | **79,55 %** | **RECONSTRUIDO / EJECUTADO** | N1 original congelado + N2 polinómico reconstruido. |
| M4 | **78,05 %** | **RECUPERADO** | Evaluación desde caché que coincide con el resultado histórico documentado. |
| MNIST Universal V24 | **97,79 %** | **REPORTADO** | Registro histórico; reproducción exacta pendiente. |

Ninguna cifra CIFAR-10 actual se presenta como reproducción limpia, auditada contra leakage y ejecutada de RAW a predicción.

## Cierre documental de Fase 1 — 22/09/2026

La Fase 1 de recuperación/auditoría queda cerrada **documentalmente**, no como reproducción histórica end-to-end. Sigue faltando el productor histórico exacto RAW → preprocesado/augmentación → PCA.

### Dependencia del batch
La auditoría ampliada ensayó **1.120 configuraciones y 2.240 repeticiones/controles**. Bajo las condiciones ensayadas, **344 configuraciones cambiaron de clase respecto a inferencia individual** y hubo **0 cambios entre repeticiones idénticas**. Las pruebas controladas muestran que la asignación del ruido recuperado puede producir esos cambios y que fijar ese ruido elimina los cambios de clase observados entre lotes en las condiciones probadas.

Esto demuestra que la ruta histórica recuperada no es invariante al contexto de batch. No demuestra que este fenómeno explique por sí solo la diferencia 80,14 % ↔ 80,17 %.

### Evidencia histórica recuperada
Se han archivado tres capturas históricas originales aportadas por el autor del proyecto. Se clasifican como **evidencia documental histórica**, no como reproducción autónoma.

Documentan, entre otros elementos:
- V23 / M4 PURIST con caché PCA, Fisher/centroides, 3.091 features, TorchLR, TorchMLP y LightGBM;
- `N1 + TTA = 77,02 %` y `N2 final = 78,05 %`, coherente con los 7.805/10.000 recuperados;
- un rescate V24 con `N1 + TTA (El Enjambre M5) = 78,45 %` y `N2 Rescatado (Linear puro) = 79,37 %`.

SHA-256 de las capturas originales:
- `248ab8ad2b6fc1cc99ee7e672c2222397848fcce1e5e05c82cdef7c42c98bf1e`
- `b9e4c95d473dfbae6d9407a786f6a576ccd30bbc0a1edd5d562b3756ab0f4298`
- `7e7893bbc0a4e82587e518b66d3dc54c640af69580b17d35170a8ed2647b1a42`

Los nombres visibles `ab_gem_v22_1_ramsafe.py` y `v24_n1.pkl` se consideran pistas de procedencia para localizar artefactos históricos. Las capturas no recuperan por sí mismas el transformador RAW→PCA perdido.

## Límites importantes de la auditoría

- Una ruta demo/evaluación M5 recuperada usa etiquetas del test al ajustar N2; esa ruta no es válida para estimar generalización sobre ese mismo test y se mantiene separada de la evidencia aceptada.
- El heatmap XAI histórico disponible está respaldado actualmente como visualización/reconstrucción PCA ponderada, no como atribución fiel demostrada de la decisión N1/N2.
- Las cifras históricas de energía no son mediciones controladas aceptadas. No se publica ningún porcentaje de ahorro energético como resultado demostrado.
- Connectome permanece como línea experimental futura, sin afirmaciones de rendimiento.

## Prioridad técnica: Clean Baseline v1

El siguiente resultado que pueda alcanzar estado **Reproducido** debe partir de datos RAW congelados, fijar el split antes de cualquier ajuste dependiente de datos, entrenar PCA/Fisher/centroides únicamente con train, generar N2 sin leakage, usar inferencia determinista, congelar entorno/semillas/hashes y reproducirse desde un entorno limpio.

Una puntuación limpia más baja tiene más valor científico que una cifra superior cuya procedencia no pueda defenderse.

## Dos líneas separadas

**Recuperación histórica / forense:** reconstruir exactamente qué hicieron los artefactos históricos sin reescribir la historia.

**Baseline limpio / investigación futura:** crear la primera referencia AB-GEN determinista, libre de leakage conocido y reproducible desde RAW. Solo después se realizarán comparaciones Green AI controladas y experimentos Connectome.

Consulta [MILESTONES.md](MILESTONES.md), [BASELINE_ACCEPTANCE.md](BASELINE_ACCEPTANCE.md), [REPRODUCIBILITY.md](REPRODUCIBILITY.md) y [GREEN_AI_BENCHMARK_PROTOCOL.md](GREEN_AI_BENCHMARK_PROTOCOL.md) para los criterios formales.

---

**Principio de comunicación:** AB-GEN se presenta con toda la fuerza que permite la evidencia, y nunca con más. Reportado, evidencia documental, recuperado, reconstruido, reproducido y validado son estados distintos.

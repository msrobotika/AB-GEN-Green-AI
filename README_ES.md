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
| Rescate V24 documentado | **79,37 %** | **EVIDENCIA DOCUMENTAL HISTÓRICA** | Captura de un N2 lineal rescatado; checkpoint/script exactos no identificados. |
| MNIST Universal V24 | **97,79 %** | **REPORTADO** | Registro histórico; reproducción exacta pendiente. |

Ninguna cifra CIFAR-10 actual se presenta como reproducción limpia, auditada contra leakage y ejecutada de RAW a predicción.

## Continuidad de evidencias — 22/09/2026

La Fase 1 sigue cerrada **documentalmente**, no como reproducción histórica end-to-end. Los originales recuperados permanecen intactos.

### Auditoría RAW

El CIFAR-10 verificado contiene **50.000 imágenes train + 10.000 test = 60.000 imágenes distintas byte a byte**. No se encontraron duplicados exactos ni dentro de cada partición ni entre train/test, y el hash del archivo permaneció intacto antes/después.

Este resultado tiene un alcance limitado: **no descarta similitud perceptual, dependencia de aumentaciones, leakage de ajuste ni una asociación incorrecta cache→RAW**. Tampoco recupera el productor histórico RAW→PCA.

### Predicciones y scores

- Se conservan **30.000 filas de predicción** de M4, M5 MASTER y Elite con `sample_id` derivado del hash de los bytes RAW oficiales.
- Inferencias congeladas de M4 y M5 MASTER coinciden **20.000/20.000** clases con las salidas previamente conservadas y mantienen **7.805** y **7.955** aciertos. Esto no eleva ninguna de las dos rutas a reproducción histórica exacta.
- La extracción de scores Elite coincide **10.000/10.000** clases con el CSV conservado y mantiene **8.017** aciertos.
- Las tres rutas suman **300.000 scores de clase** para 30.000 filas evaluadas.
- M4 exporta salidas softmax de su N2 recuperado, pero **no están certificadas como probabilidades calibradas**. M5 MASTER y Elite exportan valores Ridge `decision_function`, que **no son probabilidades**.
- Un verificador autónomo en Python estándar pasa las **30.000 filas / 300.000 scores** y rechaza tres copias alteradas deliberadamente. Certifica coherencia interna del paquete, no validación externa, procedencia cache→RAW ni reproducción histórica.

### Comparación por muestra de rutas recuperadas

| Comparación | B corrige error de A | B pierde acierto de A | Predicciones distintas | Saldo de aciertos |
|---|---:|---:|---:|---:|
| M4 → M5 MASTER | 419 | 269 | 957 | +150 |
| M4 → Elite | 628 | 416 | 1.413 | +212 |
| M5 MASTER → Elite | 445 | 383 | 1.131 | +62 |

En M5 MASTER → Elite, otras **303** imágenes cambian de clase aunque ambas rutas fallen. Por tanto, una diferencia neta de +62 aciertos no implica solo 62 predicciones distintas. Esta comparación describe ejecuciones recuperadas ya fijadas; no es una ablación causal ni una comparación contra las predicciones históricas del 80,14 %, que no se han recuperado.

### Dependencia del batch

La auditoría ampliada mantuvo los mismos 32 casos de bajo margen seleccionados sin etiquetas y probó tamaños 1/2/4/8/16/32/64, distintas posiciones y dos grupos de acompañantes:

- **1.120 configuraciones** y **2.240 ejecuciones**;
- **344 cambios de clase** frente a individual, afectando a 31 de los 32 casos ensayados;
- **0 cambios** con ruido fijo;
- **0 cambios** sin ruido;
- **0 diferencias** entre repeticiones idénticas;
- transferir a la muestra individual el ruido recibido en lote reproduce la clase en **1.120/1.120** configuraciones;
- cambiar solo acompañantes produce **0 cambios en 544 pares**.

Estas intervenciones demuestran la causa de los cambios de clase **en la matriz ensayada**. No permiten extrapolar frecuencia al test completo ni demuestran que este mecanismo explique el desfase histórico 80,14 % ↔ 80,17 %.

### Nuevas pistas de procedencia

- En el bundle Elite se encontró binariamente `_sklearn_version` seguido de **1.8.0**. Es un marcador de serialización demostrado y solo un **indicio de entorno**, no prueba del entrenamiento completo.
- Capturas M4 corroboran **Python 3.13.7 / GTX 1050 Ti** para ese contexto M4; no se atribuye ese entorno a Elite.
- La captura de rescate V24 documenta `N1 + TTA = 78,45 %` y `N2 Rescatado (Linear puro) = 79,37 %`. El `v24_n2.pkl` conservado es MLP, M4 N2 usa 30 entradas y los bundles polinómicos M5/Elite son rutas distintas. Ningún candidato queda identificado con el checkpoint lineal del 79,37 %.
- El exportador histórico referencia siete entradas ausentes en sus rutas esperadas. Que bundle, caché y RAW existan en otras carpetas no demuestra regeneración histórica.

## Límites importantes de la auditoría

- **RAW→PCA sigue NO RESUELTO.** No se ha recuperado el productor/transformador histórico ni su alcance de ajuste. El leakage PCA en test no está demostrado, pero tampoco puede descartarse.
- MASTER contiene dependencias de preprocesado/augmentación dependientes de clase anteriores a su split final; no deben atribuirse automáticamente los mismos índices o defectos a Elite sin evidencia.
- Una ruta separada `demo_inferencia.py` ajusta N2 con etiquetas test; se detectó por lectura y no constituye una evaluación válida de generalización sobre ese mismo test.
- El heatmap XAI médico histórico usa PCA/Fisher y no consulta N1/N2 ni clase objetivo en `_generate_heatmap`; es evidencia de reconstrucción PCA ponderada, no atribución fiel demostrada del clasificador.
- Las cifras históricas de energía son constantes/cálculos, no mediciones controladas. La aritmética corregida de esas constantes da aproximadamente **0,001080555 kWh por millón de inferencias**, pero un cálculo correcto sobre constantes supuestas sigue sin ser un benchmark energético.
- Connectome permanece como línea futura/documental. No se ha ejecutado entrenamiento ni arquitectura Connectome.

## Prioridad técnica: Clean Baseline v1

El siguiente resultado que pueda alcanzar estado **Reproducido** debe partir de datos RAW congelados, fijar train/validación/calibración/test antes de cualquier ajuste dependiente de datos, entrenar PCA/Fisher/centroides únicamente con train, generar N2 sin leakage, usar inferencia determinista, congelar entorno/semillas/hashes y reproducirse desde un entorno limpio.

Una puntuación limpia más baja tiene más valor científico que una cifra superior cuya procedencia no pueda defenderse.

## Dos líneas separadas

**Recuperación histórica / forense:** reconstruir exactamente qué hicieron los artefactos históricos sin reescribir la historia. Siguen abiertos RAW→PCA, script/particiones/predicciones del 80,14 %, checkpoint del rescate lineal 79,37 %, entorno histórico completo, CPU/GPU y leakage independiente.

**Baseline limpio / investigación futura:** crear la primera referencia AB-GEN determinista, libre de leakage conocido y reproducible desde RAW. Solo después se realizarán comparaciones Green AI controladas y experimentos de arquitectura.

Consulta [MILESTONES.md](MILESTONES.md), [AUDIT_NOTES.md](AUDIT_NOTES.md), [BASELINE_ACCEPTANCE.md](BASELINE_ACCEPTANCE.md), [REPRODUCIBILITY.md](REPRODUCIBILITY.md) y [GREEN_AI_BENCHMARK_PROTOCOL.md](GREEN_AI_BENCHMARK_PROTOCOL.md) para los criterios formales.

---

**Principio de comunicación:** AB-GEN se presenta con toda la fuerza que permite la evidencia, y nunca con más. Reportado, evidencia documental, recuperado, reconstruido, reproducido y validado son estados distintos.

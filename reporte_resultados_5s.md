# Reporte de resultados FHCP

## 1. Alcance y lectura de las figuras

El análisis corresponde a `results_fhcp_all_5s` y cubre 723 instancias, con tamaños entre 66 y 9528 vértices. Las figuras de tasa de éxito y costo promedio están divididas en 17 páginas de 45 instancias; las figuras de convergencia contienen una gráfica por instancia.

La función objetivo es `c(pi)`, el número de aristas consecutivas faltantes. Por tanto:

- `c(pi) = 0`: ciclo hamiltoniano encontrado.
- Un valor mayor indica una solución incompleta; cuanto menor, mejor.
- En el heatmap de éxito, cada celda muestra `éxitos/corridas`.

**Advertencia de configuración:** aunque la carpeta se llama `all_5s`, los datos y las figuras indican un límite de aproximadamente 30 segundos por corrida (`30 s máx. por corrida`). Las conclusiones corresponden a 30 s, no a 5 s.

## 2. Resultado global

Se ejecutaron 21.683 corridas de los seis algoritmos metaheurísticos y 717 corridas de `LKH`. Las corridas internas tienen normalmente cinco semillas por instancia y algoritmo; `LKH` tiene una corrida por instancia disponible.

| Algoritmo | Corridas | Éxitos | Tasa de éxito | Costo normalizado medio | Precisión media | Instancias resueltas | Rango medio |
|---|---:|---:|---:|---:|---:|---:|---:|
| ABC | 3.615 | 111 | 3,07% | 0,0122 | 0,9878 | 25 | 1,358 |
| SA | 3.615 | 67 | 1,85% | 0,0219 | 0,9781 | 22 | 3,641 |
| GA | 3.615 | 42 | 1,16% | 0,0271 | 0,9729 | 11 | 2,464 |
| DE | 3.613 | 36 | 1,00% | 0,0284 | 0,9716 | 8 | 3,969 |
| PSO | 3.610 | 36 | 1,00% | 0,0284 | 0,9716 | 8 | 3,972 |
| ACO | 3.615 | 13 | 0,36% | 0,0655 | 0,9345 | 10 | 5,593 |
| LKH | 717 | 10 | 1,39% | No comparable | No comparable | 10 | No comparable |

### Interpretación

1. **ABC es el mejor algoritmo global.** Tiene la mayor tasa de éxito, el menor costo normalizado, la mayor precisión y el mejor rango medio. También resuelve 25 instancias, más que cualquier otro método.
2. **SA es el segundo método más eficaz para encontrar ciclos**, con 67 éxitos y 22 instancias resueltas. En grafos pequeños puede competir directamente con ABC.
3. **GA obtiene el segundo mejor rango medio**, aunque su tasa de éxito es inferior a la de SA. Esto indica que suele producir costos relativamente bajos aun cuando no alcanza `c(pi)=0`.
4. **DE y PSO se comportan prácticamente igual**: misma tasa de éxito, mismo costo normalizado y casi el mismo rango. No hay evidencia descriptiva de una ventaja práctica clara entre ambos.
5. **ACO es el método más débil en este experimento**: menor tasa de éxito, menor precisión y mayor costo residual medio.
6. La precisión media es alta para todos porque la mayoría de las soluciones tienen pocos errores respecto al tamaño del grafo; no debe confundirse con haber encontrado un ciclo válido. La métrica decisiva para HCP es la tasa de éxito (`c(pi)=0`).

## 3. Efecto del tamaño del grafo

La dificultad crece muy rápidamente con `n`:

| Tamaño de la instancia | Éxito conjunto de los algoritmos internos |
|---|---:|
| 66-250 | 12,00% |
| 251-500 | 6,83% |
| 501-1000 | 4,17% |
| 1001-2000 | 0,42% |
| 2001-4000 | 0,00% |
| 4001-9528 | 0,00% |

Los seis algoritmos internos no encontraron ningún ciclo en las 412 instancias con más de 2.000 vértices durante el límite utilizado. El último éxito observado de cada algoritmo se encuentra en `n=1123`, lo que marca una frontera experimental clara: a partir de ahí, las soluciones siguen mejorando el costo, pero no alcanzan la solución exacta.

### Rendimiento por intervalos

- **66-250 vértices:** ABC alcanza 32,0% de éxito y SA 28,0%; son los métodos claramente dominantes. ACO llega a 6,67%, GA a 4,0%, y DE/PSO a 0,67%.
- **251-500:** ABC mantiene ventaja con 18,10%. SA baja a 6,67%; GA queda en 5,24%; DE y PSO en 4,76%; ACO en 1,43%.
- **501-1000:** ABC, GA, DE y PSO empatan en 5,56%; SA baja a 2,78% y ACO no obtiene éxitos.
- **1001-2000:** todos caen prácticamente a cero. ABC, GA y DE/PSO alcanzan 0,60%; SA solo 0,12%; ACO no resuelve ninguna.
- **Más de 2.000:** ningún algoritmo produce un ciclo hamiltoniano, aunque ABC conserva el menor costo normalizado dentro de los métodos internos.

## 4. Lectura de los heatmaps

El heatmap de tasa de éxito muestra un patrón muy concentrado:

- Las celdas oscuras se concentran en las primeras páginas, donde están las instancias más pequeñas.
- ABC presenta la mayor cantidad de celdas `5/5` o `4/5`, señal de estabilidad entre semillas.
- SA también muestra bloques de `5/5`, especialmente en grafos pequeños, pero pierde capacidad antes que ABC al aumentar `n`.
- GA, DE y PSO tienen muchas celdas `0/5`; cuando tienen éxito, suele ser en instancias concretas y no en un rango amplio.
- ACO tiene pocas celdas distintas de `0/5` y su mapa de costos mantiene valores residuales más altos.
- `LKH` aparece con `0/1` o `1/1`: su tasa no es directamente comparable con la de los métodos de cinco corridas, pero sirve como referencia puntual.

El heatmap de costo promedio muestra que:

- ABC mantiene sistemáticamente los valores más bajos entre los algoritmos internos.
- SA suele quedar cerca de ABC en las instancias pequeñas y medianas.
- GA es intermedio.
- DE y PSO forman una pareja de comportamiento casi idéntico y normalmente dejan más aristas faltantes que ABC o SA.
- ACO suele presentar el mayor costo promedio.
- En grafos grandes, las diferencias de costo siguen siendo visibles aunque todos fallen en el criterio exacto; esto significa que el algoritmo aún mejora la permutación, pero el presupuesto no basta para completar el ciclo.

## 5. Convergencia

Las gráficas individuales de convergencia representan la mediana de cinco corridas de cada algoritmo interno.

En instancias pequeñas, como `graph1.hcp`, varias curvas llegan rápidamente a valores bajos. ABC alcanza `c(pi)=0` alrededor de los primeros segundos en la mediana, mientras SA tarda más; ACO, GA, DE y PSO quedan en valores residuales en esa instancia.

En una instancia grande, como `graph1001.hcp`, ninguna curva llega cerca de cero. ABC es la mejor curva visible y reduce el costo aproximadamente desde la zona de 550 hasta la zona de 430, pero todavía queda muy lejos de un ciclo válido. SA, GA, DE y PSO se estabilizan alrededor de 500-550, y ACO queda claramente peor, cerca de 900.

El patrón general de las 723 curvas es, por tanto:

1. ABC ofrece la mejor mejora continua y la mejor solución final.
2. SA puede converger muy bien en instancias pequeñas, pero no conserva esa ventaja al crecer `n`.
3. ACO converge a soluciones de peor calidad en grafos grandes.
4. DE y PSO muestran curvas muy parecidas y una mejora limitada.
5. El estancamiento antes de `c(pi)=0` es el comportamiento dominante para las instancias grandes.

## 6. Precaución estadística

El archivo `estadistica.json` contiene valores `NaN` para la prueba de Friedman. Por ello, el rango medio debe interpretarse como una comparación descriptiva de costos por instancia, no como una diferencia estadísticamente demostrada. Tampoco debe usarse este experimento para afirmar que ABC es significativamente superior sin repetir la prueba con datos completos y una configuración estadística que gestione los empates y valores faltantes.

## 7. Comparación con LKH

`LKH` resolvió 10 de 717 instancias disponibles, con una tasa de 1,39%. Esta cifra no debe interpretarse como inferioridad directa frente a ABC porque:

- LKH tiene una sola corrida por instancia.
- Su configuración y criterio de tiempo no son necesariamente idénticos.
- La tabla global de ranking excluye LKH de la comparación estadística principal.

Su inclusión en los heatmaps es útil para identificar coincidencias puntuales (`1/1`) y diferencias de cobertura, pero no para establecer un ranking experimental limpio.

## 8. Conclusiones

El resultado principal es que **ABC es la alternativa recomendada para este conjunto y presupuesto**, especialmente si el objetivo es maximizar la probabilidad de encontrar ciclos y minimizar las aristas faltantes cuando no lo consigue. **SA** es una buena segunda opción en grafos pequeños. **GA** puede ser competitivo en calidad residual, pero no en tasa de éxito. **ACO** no resulta recomendable bajo esta configuración.

La limitación dominante no es solo el algoritmo: es la escalabilidad. Con 30 segundos y cinco corridas, los métodos encuentran soluciones válidas principalmente hasta aproximadamente 1.123 vértices y no resuelven instancias por encima de 2.000. Para estudiar una mejora real en grafos grandes habría que aumentar el presupuesto, ajustar parámetros por tamaño, utilizar una estrategia híbrida o comparar con una configuración homogénea de LKH.

## 9. Archivos de evidencia

- [resumen_algoritmos.csv](results_fhcp_all_5s/resumen_algoritmos.csv)
- [resumen_instancia_algoritmo.csv](results_fhcp_all_5s/resumen_instancia_algoritmo.csv)
- [tasa_exito.png](results_fhcp_all_5s/figuras/tasa_exito.png) y páginas `tasa_exito_002.png` a `tasa_exito_017.png`
- [costo_promedio.png](results_fhcp_all_5s/figuras/costo_promedio.png) y páginas `costo_promedio_002.png` a `costo_promedio_017.png`
- [estadistica.json](results_fhcp_all_5s/estadistica.json)

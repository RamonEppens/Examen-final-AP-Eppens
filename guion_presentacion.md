# Guión hablado — Examen Final Análisis Predictivo
### Predicción de ratings de juegos de mesa (BGG) · ~13-14 min hablados + margen

**Convenciones:** [ENTER] = avanzás un paso en la web. Lo que está entre paréntesis y en cursiva son indicaciones para vos, no se dicen. Los tiempos son orientativos por acto.

### Nota de sincronización con la web (agregada en esta revisión)

Se recorrió `presentacion/index.html` paso por paso — incluyendo los builds internos de cada slide (`STEP_STAGES` en `charts.js`) — y se contrastó contra cada [ENTER] de este guión. Los cambios están marcados inline con `<!-- SYNC: ... -->`; podés buscarlos y borrarlos una vez revisados. Resumen por acto:

- **Actos 1-2 e inicio de Acto 3:** se sacaron 5 [ENTER] que no tenían pantalla propia. La web solo cambia de pantalla dos veces en todo este tramo (hero → "El problema" → pipeline de Acto 3); Acto 2 completo ("La apuesta") se dice sobre la misma pantalla que el cierre de Acto 1.
- **Acto 4 (EDA), las 4 preguntas:** se agregó 1 [ENTER] nuevo en cada una. La web muestra la pregunta + gráfico primero, y recién en un segundo build revela la respuesta y el chip de "Decisión" — el guión los tenía como un solo bloque.
- **Acto 5:** se sacó 1 [ENTER] interno; la pantalla de evaluación (línea de tiempo train/holdout) se revela entera de una sola vez.
- **Acto 6:** se sacaron 2 [ENTER] y se agregó 1 nuevo, reubicado exactamente en "(Pantalla verde.)" — que es donde la web realmente pasa a la pantalla de designer_enc.
- **Acto 7:** se sacó 1 [ENTER] (los contadores ya están visibles al entrar a la pantalla del modelo final) y se movió el párrafo de Catan, que en la web vive en la pantalla de los contadores, no en la de importances.
- **Acto 8:** se sacaron 2 [ENTER] internos; la pantalla de cierre se revela entera de una sola vez.
- **No se encontró ningún paso de la web sin ninguna línea hablada cerca** (el caso "pantalla muda" que se pedía señalar con `[pantalla de transición — no se habla]`) — los 16 pasos del cuerpo principal (Actos 1 a 8) tienen todos alguna cobertura. El único paso de la web que queda totalmente fuera de esta secuencia es el Anexo interactivo (`s-anexo`, tecla `A`), que es material de respaldo aparte y no se toca acá — ya está cubierto por la sección "ANEXO DEL GUIÓN" más abajo, que es de otra naturaleza (respuestas preparadas, no pantallas).

---

## ACTO 1 — EL PROBLEMA (~1 min)

*(Pantalla de apertura. Arrancá sin apuro, mirando a los profes, no a la pantalla.)*

Buenas. Les quiero contar un problema que tiene cualquier editorial de juegos de mesa.

[ENTER]

Todos los años les llegan cientos de propuestas de diseñadores. Prototipos, pitches, reglamentos.

Producir uno en serio —arte, componentes, tirada mínima— cuesta decenas de miles de dólares. Y la mayoría de los juegos que se publican pasan sin pena ni gloria.

Entonces la pregunta de negocio es simple: **¿cuáles elegir?** Hoy esa decisión se toma con playtesting y olfato editorial. La idea de este trabajo es sumarle una herramienta cuantitativa.

<!-- SYNC: se sacaron los [ENTER] que separaban estos tres párrafos. La pantalla "El problema" (s-problema) revela sus 3 tarjetas juntas al llegar y no vuelve a cambiar hasta el Acto 3 — este bloque y todo el Acto 2 se dicen sin avanzar de pantalla. -->

---

## ACTO 2 — LA APUESTA (~45 seg)

<!-- SYNC: Acto 2 no tiene pantalla propia en la web — se sigue viendo "El problema" (s-problema). Se sacaron los dos [ENTER] de este acto; el próximo avance real de pantalla es el que aparece marcado en el Acto 3, antes de "(Nodo 1 del pipeline.)". -->

La apuesta es esta: cuando un prototipo llega a una editorial, su ficha técnica ya está definida. Qué tan complejo es, qué mecánicas usa, para cuántos jugadores, cuánto dura. Todo eso se conoce **antes** de gastar un dólar en producción.

La pregunta que este proyecto responde: ¿esa ficha técnica anticipa la recepción del público? Y si sí, ¿cuánto?

---

## ACTO 3 — LA MATERIA PRIMA (~2 min)

Para responderla necesitaba dos cosas: el veredicto del público, y la ficha de cada juego. Las dos salen de BoardGameGeek, que es la base de datos de juegos de mesa más grande del mundo — millones de usuarios que puntúan juegos del 1 al 10.

<!-- SYNC: se sacó el [ENTER] que había antes de este párrafo (parte del tramo sin cambio de pantalla de Actos 1-2). El siguiente [ENTER] es el primer avance real desde "El problema". -->

[ENTER]

*(Nodo 1 del pipeline.)* Primera fuente: el ranking diario de BGG. Ahí está el rating promedio de treinta mil ochocientos juegos. Ese es mi target: la variable `average`. Pero el ranking no dice nada de **cómo es** cada juego.

[ENTER]

*(Nodo 2.)* Segunda fuente: la API oficial de BGG. Para cada juego, la ficha completa: complejidad —que la comunidad vota en una escala de 1 a 5 y llaman *weight*—, mecánicas, cantidad de jugadores, duración, edad mínima, categorías. Acá hubo una anécdota de datos reales: a mitad del proyecto BGG cambió su política y la API empezó a exigir aplicaciones registradas. Registré una app académica, me la aprobaron, y el pipeline siguió con autenticación.

[ENTER]

*(Nodos que se unen.)* Las dos fuentes se unen por el ID del juego. Veredicto más ficha, juego por juego: una tabla donde cada fila tiene lo que el juego **es** y cómo lo **puntuó** la comunidad.

[ENTER]

*(Contador de limpieza. Dejá que corra la animación.)* De los treinta mil ochocientos sesenta y cuatro del ranking: saco duplicados, saco años inválidos —juegos sin fecha real o listados a futuro— y sobre todo saco los juegos con menos de cincuenta votos. Enseguida muestro por qué. Quedan **veinticuatro mil doscientos cincuenta y un juegos confiables**. Esa es la base de todo lo que sigue.

---

## ACTO 4 — CONOCER EL TERRENO / EDA (~3 min)

[ENTER]

Antes de modelar, cuatro preguntas al dataset. Y cada respuesta habilitó una decisión de diseño del modelo — no hay ningún gráfico decorativo acá.

[ENTER]

**Primera pregunta: ¿todos los ratings valen lo mismo?** *(Gráfico del embudo.)*

<!-- SYNC: [ENTER] agregado acá. En la web, la pregunta + el gráfico aparecen solos primero; la respuesta y el chip de "Decisión" son un segundo build que se revela con otro avance. -->

[ENTER]

No. Miren la forma de embudo: con pocos votos, el rating de un juego es una lotería — puede estar en cualquier lado entre 1 y 10. A medida que acumula votos, se estabiliza. **Decisión:** el modelo se entrena solo con juegos de cincuenta votos o más. Pierdo un veinte por ciento de las filas, gano un target en el que puedo confiar.

[ENTER]

**Segunda: ¿la vara del público es estable en el tiempo?** *(Gráfico temporal.)*

<!-- SYNC: mismo caso — [ENTER] agregado antes de la respuesta. -->

[ENTER]

Tampoco. La media histórica era seis puntos y estaba planchada hasta 2010. De ahí en adelante sube sin parar: los juegos de 2026 promedian siete y medio. La comunidad puntúa cada vez más alto. **Decisión:** si la vara se mueve con el tiempo, no puedo evaluar el modelo mezclando pasado y futuro al azar. Esto define toda la evaluación — lo ven en dos minutos.

[ENTER]

**Tercera: ¿qué pesa más en el rating?** *(Scatter weight vs. rating.)*

<!-- SYNC: mismo caso. -->

[ENTER]

La complejidad. Correlación de 0.55 — de lejos la señal más fuerte. A la comunidad de BGG le gustan los juegos profundos. **Decisión:** weight es la feature central del modelo.

[ENTER]

**Cuarta pregunta, y esta es la sorpresa del EDA: ¿los juegos modernos son más complejos? ¿Será por eso que ratean mejor?** *(Gráfico year×weight.)*

<!-- SYNC: mismo caso. -->

[ENTER]

**No.** Correlación prácticamente cero entre año y complejidad. Los juegos no cambiaron su naturaleza — la que cambió es la comunidad, que puntúa distinto. El año no mide evolución del producto: mide el sesgo de la vara. Tenerlo claro importa para interpretar todo lo que viene.

---

## ACTO 5 — LA PRUEBA HONESTA (~1.5 min)

[ENTER]

¿Cómo se evalúa un modelo cuyo trabajo va a ser predecir juegos **que todavía no existen**? De la única manera honesta: simulando exactamente eso.

*(Línea de tiempo del split.)* Partí los datos por año. El modelo entrena con todo lo publicado hasta 2023 — veintidós mil juegos. Y rinde examen contra los juegos de 2024 a 2026 — dos mil doscientos cuarenta y uno que **nunca vio y que no existían** en su época de entrenamiento. Sin mezclar, sin espiar.

La métrica es RMSE: el error típico de predicción, en la misma escala del rating. Si el RMSE es 0.6, quiere decir que típicamente le erro más o menos 0.6 puntos al rating final de un juego. Durante el desarrollo usé validación cruzada dentro del pasado; el holdout del futuro se tocó solamente para las evaluaciones finales.

<!-- SYNC: se sacó el [ENTER] que separaba estos dos párrafos. La pantalla de evaluación (línea de tiempo train/holdout) se revela entera de una sola vez, sin build interno. -->

---

## ACTO 6 — EL TORNEO (~2.5 min)

[ENTER]

Con la cancha marcada, el torneo. *(Escalera de RMSE.)* De abajo hacia arriba: predecir siempre la media —el baseline tonto— erra 0.86 puntos. Una regresión lineal con las variables numéricas baja a 0.65. Ridge y Lasso con todas las features, 0.62. Random Forest, 0.58. Y los gradient boosting —XGBoost y LightGBM— empatan en 0.57. Ahí está el podio, y la mejora de los boosting sobre los lineales me dice que hay interacciones y no linealidades reales en el problema.

Sobre esa base probé features nuevas en dos rondas. Quedaron las que mejoraron de forma robusta: el ratio entre duración máxima y mínima, el rango de jugadores, y diez familias de mecánicas. Se descartaron las que no: interacciones explícitas, términos cuadráticos — el boosting ya las captura solo.

Y ahora la historia más importante del proyecto. Probé codificar el **historial del diseñador**: qué rating promedio tienen sus juegos anteriores.

<!-- SYNC: se sacaron los [ENTER] que había antes de "Sobre esa base..." y antes de este párrafo. La pantalla "Selección de modelos" (escalera de RMSE) no cambia hasta acá — los tres párrafos se dicen seguidos sobre ella. El próximo [ENTER] se reubicó exactamente en el punto donde la pantalla realmente se pone verde. -->

[ENTER]

*(Pantalla verde.)* En validación cruzada, la mejor feature de todas: baja el error 0.015. Sin leakage — lo verifiqué con encoding anidado estricto.

[ENTER]

*(Pantalla terracota. Pausa antes de hablar.)* Pero contra el futuro... **colapsa.** Sube el error 0.089. ¿Por qué? Porque el treinta por ciento de los diseñadores de 2024 a 2026 son **debutantes** — no tienen historial. El modelo había aprendido que "sin señal del diseñador" significaba "diseñador mediocre", y en el futuro significa "no sabemos quién es". Dos cosas distintas, misma codificación.

[ENTER]

*(Pantalla de la lección.)* La lección metodológica que me llevo de este trabajo: **pasar la validación cruzada no alcanza.** Una feature puede ser impecable hacia adentro y romperse contra el futuro. La descarté — y la pude descartar únicamente porque la evaluación temporal existía.

---

## ACTO 7 — EL ELEGIDO (~2 min)

[ENTER]

El modelo final: **LightGBM**, con noventa y dos features. ¿Por qué LightGBM y no XGBoost, si empataron? Porque cuando la diferencia de rendimiento es estadísticamente ruido —y acá era de ocho diezmilésimas— se decide por criterios prácticos: entrena más rápido y maneja valores faltantes de forma nativa, que mi dataset tiene sin imputar. Los hiperparámetros los validé con doscientos trials de Optuna: la búsqueda no encontró nada mejor que la configuración elegida. El techo del modelo no está en el ajuste fino — está en la información disponible.

*(Contadores.)* Los números finales, contra el futuro: RMSE 0.64, MAE 0.47, R² 0.30. ¿Es bueno errarle 0.64 puntos? Para separar un candidato de siete y medio de uno de seis —que es la decisión editorial real— sí, alcanza y sobra. Sobre el R²: parece bajo comparado con el 0.56 de la validación cruzada, pero ojo — el error casi no creció. Lo que se achicó es la **varianza a explicar**: los juegos recientes ratean todos parecido por el sesgo que vimos, y con menos diferencias que explicar, el mismo error rinde un R² menor. No es un modelo peor: es una vara distinta.

Y una limitación que asumo de frente: el modelo **subestima a los fenómenos**. A Catan, a Carcassonne. Porque lo que los hizo fenómenos —el momento histórico, el boca a boca, la ejecución— no está en su ficha técnica. Y está bien que así sea.

<!-- SYNC: se sacó el [ENTER] que había antes de "(Contadores.)" — los tres contadores (RMSE/MAE/R²) ya están visibles apenas se entra a la pantalla del modelo final, junto con la frase de Catan; no hay build separado para ellos. También se movió el párrafo de Catan: en el guión original iba después de "(Importances.)", pero en la web esa frase vive en la MISMA pantalla que los contadores, no en la de importances — se dice antes del próximo avance, no después. -->

[ENTER]

*(Importances.)* Qué mira el modelo: complejidad primero, año segundo —el sesgo de la vara, bien entendido—, después duración, edad mínima, riqueza de mecánicas. Todo interpretable, todo coherente con el EDA.

---

## ACTO 8 — ¿DE QUÉ SIRVE TODO ESTO? (~1.5 min)

[ENTER]

Cierro con la pregunta del principio: ¿de qué le sirve esto a la editorial? *(Mockup de la herramienta.)* Así funcionaría en producción: el equipo editorial carga la ficha del prototipo — complejidad, mecánicas, jugadores, duración — y obtiene el rating esperado.

Tres usos concretos: **priorizar** el pipeline de desarrollo cuando hay cien pitches y presupuesto para cinco. **Ajustar** decisiones de diseño — ¿esta duración, con esta complejidad, para este público? Y **fundamentar** apuestas con datos, no solo con olfato.

Igual de importante es lo que **no** hace: no detecta al próximo Catan. Es un filtro, no un oráculo — descarta los errores evitables y deja la apuesta creativa donde tiene que estar: en las personas.

*(Frases finales. Ritmo lento, es el cierre.)* Tres cosas me llevo de este trabajo. Que la ficha técnica de un juego anticipa una parte real del veredicto del público. Que **evaluar contra el futuro cambia las decisiones** — literalmente me hizo descartar la que parecía la mejor feature. Y que las ganancias que no son robustas, se rechazan: me pasó con el diseñador, con las features cuadráticas y con el tuning.

El código, los datos y esta presentación están en el repositorio. Muchas gracias — quedo abierto a preguntas.

<!-- SYNC: se sacaron los dos [ENTER] internos de este acto. La pantalla de cierre ("Limitaciones y cierre": lista de límites + 3 frases de impacto + botón al repo) se revela entera de una sola vez al entrar — es el último paso del cuerpo principal, así que los tres párrafos del Acto 8 se dicen seguidos sobre ella, sin más avances. -->

---
---

# ANEXO DEL GUIÓN — Respuestas preparadas para preguntas probables

**¿Por qué este dataset?**
Cumple todo lo que pide la consigna con margen: 24 mil observaciones, más de 90 features tras el encoding, target continuo claro, y es actualizable a futuro por diseño — el ranking se publica a diario y la API es oficial con mi app aprobada. Y sostiene un caso de negocio genuino, no inventado sobre el dataset.

**¿Qué variables están disponibles al momento de predecir?**
Solo las de la ficha de diseño: complejidad, mecánicas, categorías, jugadores, duración, edad mínima. Excluí explícitamente todo lo que no existe pre-lanzamiento o deriva del target: cantidad de votos, bayes_average y rank — estas dos últimas son funciones directas del target, sería leakage.

**¿Por qué 50 votos y no 30 o 100?**
BGG ya exige 30 para rankear, así que 30 era no filtrar nada. Con 50 elimino la franja de mayor varianza del target reteniendo el 80% de los datos. Con 100 perdía casi la mitad del dataset y sesgaba hacia juegos populares — incoherente con un caso de uso que evalúa prototipos de nicho. Está la tabla de umbrales en el anexo de la presentación.

**¿El weight se conoce antes del lanzamiento?**
Es una estimación editorial en la etapa de pitch —la editorial sabe si el prototipo es un party game o un euro pesado— y BGG la refina después con votos. Es la feature con más ruido de disponibilidad, lo reconozco como limitación; para producción se usaría la complejidad estimada por el equipo.

**¿Por qué RMSE y no MAE como métrica principal?**
Penaliza más los errores grandes, que son los caros para el negocio: decirle a la editorial que un juego de 5.5 va a sacar 8 es mucho peor que errarle por décimas. MAE lo reporto como complemento.

**¿Por qué el holdout es temporal y no un split aleatorio?**
Porque el modelo en producción predice juegos futuros, y el EDA mostró que el target tiene tendencia temporal fuerte. Un split aleatorio evalúa un escenario que no existe y sobreestima el rendimiento. La prueba de que importa: designer_enc pasaba el split aleatorio y colapsaba en el temporal.

**¿Cuántas veces tocaste el holdout?**
Tres: modelo base, la configuración F8 con designer_enc, y la configuración final. Toda la selección fina de features e hiperparámetros se hizo en validación cruzada. Lo tengo documentado en el notebook 02.

**¿Por qué no imputaste los faltantes?**
LightGBM los maneja nativamente y aprende de la ausencia. Para los modelos lineales del torneo sí imputé por mediana dentro del pipeline, ajustada solo en train. Además convertí los ceros centinela de BGG a NaN — en BGG, cero significa "sin dato".

**¿Probaste redes neuronales / otros modelos?**
Con datos tabulares de este tamaño, el estado del arte son los gradient boosting — la literatura y la práctica de Kaggle lo respaldan consistentemente. El torneo cubrió las familias relevantes: lineales regularizados, bagging y boosting.

**¿Qué harías con más tiempo?**
La única mejora con potencial real es información nueva: las descripciones de texto de los juegos vía embeddings, y quizás el arte de tapa con visión. Tuning ya hice —200 trials, ganancia nula—, y publisher encoding repetiría el problema del diseñador. También me gustaría reentrenar con ventana móvil para producción real.

**¿El modelo sirve para otra cosa que ratings?**
El pipeline es reutilizable para cualquier target de BGG — por ejemplo, predecir el weight de un juego nuevo, o clasificar si entra al top-1000. El caso de negocio elegido es el que mejor mapea a una decisión editorial concreta.

---

## Tips de ensayo

1. **Cronometrate por acto** con los tiempos del guión — el total da ~13-14 min, dejando margen para respirar. Si te pasás, el acto 6 es donde más grasa hay para cortar (la pantalla de features descartadas puede ser una frase).
2. **Ensayá las transiciones de designer_enc**: la pausa antes de "pero contra el futuro... colapsa" es el momento más teatral de la presentación. No la apures.
3. **No leas la pantalla** — está diseñada para que no haga falta. El guión es para ensayar; el día del examen, las frases de impacto en pantalla son tus recordatorios.
4. Los números que conviene saber de memoria: 24.251 juegos · ρ=0.55 weight · 6.0→7.5 el sesgo · 0.856→0.569 la escalera · −0.015/+0.089 designer_enc · 29.5% debutantes · RMSE 0.64 final.

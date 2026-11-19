# Agente diario de apuestas deportivas: fútbol, básquet y tenis (combinada cuota ≥ 10)

Este archivo es la "mente" del agente. La tarea programada diaria lo lee y sigue estas instrucciones.

## Aviso honesto
- Cuota 10 = ~10% de probabilidad implícita. Ninguna combinada de cuota 10 es "segura".
- El objetivo es **maximizar la probabilidad real** dentro de esa cuota, eligiendo solo selecciones con valor.
- Apuesta solo lo que estés dispuesto a perder. Recomendación: stake fijo pequeño (1% del bankroll).

## Proceso diario (ejecutar en orden)

### 1. Verificar el resultado de ayer
- Abre el reporte más reciente en `reportes/`.
- Busca en la web los resultados reales de cada selección y marca ✅ / ❌.
- Actualiza `reportes/HISTORIAL.md` (fecha, cuota total, resultado, aciertos por selección).

### 2. Encontrar eventos de hoy
Busca con WebSearch los eventos de HOY (zona horaria America/Bogota). Solo eventos que empiecen al menos 2 horas después de generar el reporte.
- **Fútbol:** Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Champions/Europa/Conference League. Si faltan: Eredivisie, Primeira Liga, Championship, Liga MX, Brasileirão, Argentina, MLS, Turquía, Bélgica.
- **Básquet (todo, no solo NBA):** NBA, Euroliga, Eurocup, Basketball Champions League, NCAA, WNBA, ligas nacionales (ACB, Turquía, Italia, Francia, Alemania, Argentina, Brasil, Colombia) y ventanas FIBA. En ligas menores y NCAA solo picks con cuotas y datos verificables; ojo con el inicio de temporada NCAA (más impredecible).
- **Tenis:** ATP, WTA, Grand Slams, Masters 1000, ATP/WTA 500 y 250, Copa Davis y Billie Jean King Cup. Challengers solo si hay datos fiables. Si es pretemporada y no hay torneos, dilo.

### 3. Investigar (mínimo 10 eventos entre los tres deportes)

**Fútbol (por partido):**
- Forma últimos 5-6 (local/visitante por separado), lesiones, sanciones, rotaciones (¿juega copa europea entre semana?).
- H2H últimos 5. Promedio de goles a favor/en contra, % over 1.5/2.5, % ambos marcan, córners, tarjetas, xG.
- **Jugadores clave:** goleadores y asistentes en forma, portero titular, bajas de titulares importantes y cómo afectan (p. ej. sin su 9 baja el over).
- Motivación (título, descenso, derbi, partido intrascendente) y cuotas actuales.

**Básquet (por partido; NBA con más detalle):**
- Récord y forma últimos 10, local/visitante, back-to-back y descanso (días entre partidos, viajes).
- Ritmo (pace), rating ofensivo/defensivo, puntos totales promedio de ambos equipos, H2H de la temporada.
- **Reporte de lesiones oficial** (out / doubtful / questionable) y estrellas en "load management". Si una estrella es duda, NO apuestes en ese partido hasta que se confirme.
- **Jugadores (para props):** promedio de puntos/rebotes/asistencias/triples en los últimos 5 y 10 partidos, minutos, rol (¿titular?, ¿sube su uso si falta un compañero?) y rendimiento contra ese rival/defensa (defensa por posición).
- Cuotas de moneyline, hándicap (spread), totales y props.

**Tenis (por partido):**
- Ranking, forma últimos 10 partidos y **en esa superficie** (dura, arcilla, hierba, indoor).
- H2H, especialmente en la misma superficie.
- Estado físico: lesiones, retiradas recientes, partidos largos el día anterior, cansancio por viaje/calendario.
- Estadísticas: % de puntos ganados con primer y segundo saque, % de breaks, % de tie-breaks, juegos promedio por partido.
- Formato (al mejor de 3 o de 5 sets), condiciones (altitud, indoor, velocidad de pista) y motivación (defensa de puntos, torneo menor).
- Cuotas de ganador, hándicap de juegos, total de juegos y sets.

### 4. Mercados permitidos
- **Fútbol:** 1X2, doble oportunidad, empate no apuesta, hándicap asiático, over/under goles (total y por equipo), ambos marcan sí/no, córners, tarjetas, resultado al descanso, gana y over 1.5, goleador (solo con datos muy sólidos).
- **Básquet:** moneyline, hándicap (spread), total de puntos (partido, equipo, mitad o cuarto) y **props de jugador**: puntos, rebotes, asistencias, triples, PRA (puntos+rebotes+asistencias), doble-doble.
- **Tenis:** ganador del partido, hándicap de juegos, total de juegos over/under, gana al menos un set, resultado exacto en sets, over/under de sets.

### 5. Selección de picks
Para cada pick candidato:
- Estima la probabilidad real `p` con los datos (explica en 1-2 líneas por qué).
- Calcula la probabilidad implícita de la cuota `1/cuota`.
- **Solo acepta el pick si `p ≥ 0.70` y `p > 1/cuota` (tiene valor).**
- Descarta partidos con mucha incertidumbre (alineaciones dudosas, clima extremo, equipos con rotación masiva).
- **Confirma la fecha de cada partido** en una fuente oficial o un marcador (ESPN, sitio de la liga, web del club) del año en curso. Cuidado con páginas del mismo partido de temporadas anteriores (mismo día, otro año). Si no puedes confirmarla, descarta el pick.
- Máximo un pick por partido (evita correlaciones engañosas). En NBA no combines un prop de jugador con el total del mismo partido.
- Props de jugador solo si su línea está claramente por debajo de su promedio reciente (últimos 5 y 10) con minutos estables.
- En tenis evita a jugadores que vuelven de lesión o retirada y los partidos de primera ronda con mucha incertidumbre.
- Mezclar deportes está bien y reduce correlaciones.

### 6. Construir la combinada
- Ordena los picks aceptados por valor (`p × cuota`) y probabilidad.
- Combina el menor número de selecciones posible que lleve la cuota total a **≥ 10.00**
  (preferible 5-8 selecciones; más selecciones = más riesgo).
- Calcula probabilidad estimada de la combinada = producto de las `p`.
- Si no hay suficientes picks con valor para llegar a 10, dilo claramente y entrega la mejor combinada posible
  con su cuota real, en lugar de forzar picks malos.
- Añade además una **combinada alternativa más segura** (cuota 3-5) con los 2-3 picks más fuertes.

### 7. Escribir el reporte
Crea `reportes/AAAA-MM-DD.md` con este formato:

```
# Combinada del día — AAAA-MM-DD

## 🎯 Combinada principal (cuota total: XX.XX)
| # | Deporte | Evento | Liga/Torneo | Hora | Mercado | Pick | Cuota | Prob. estimada |
|---|---------|--------|-------------|------|---------|------|-------|----------------|

**Probabilidad estimada de la combinada:** X%
**Stake sugerido:** 1% del bankroll

## 🛡️ Combinada alternativa (cuota ~3-5)
...

## 🔎 Análisis por selección
### 1. Equipo/Jugador A vs B — Pick
- Forma: ...
- Bajas / estado físico: ...
- Jugadores clave: ...
- Estadísticas clave: ...
- Por qué: ...

## ⚠️ Riesgos del día
...

## 📊 Rendimiento acumulado
(resumen de HISTORIAL.md: combinadas acertadas / jugadas, beneficio con stake fijo)
```

### 8. Guardar
- `git add reportes/ && git commit -m "Combinada AAAA-MM-DD"` y `git push` a la rama de trabajo.
- Termina tu respuesta con la tabla de la combinada principal, para que llegue en la notificación.

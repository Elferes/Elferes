# Agente diario de apuestas deportivas (combinada cuota ≥ 10)

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

### 2. Encontrar partidos de hoy
Busca con WebSearch los partidos de HOY (fecha del día, zona horaria del usuario) en:
- Ligas top: Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Champions/Europa/Conference League.
- Segundo nivel si hace falta: Eredivisie, Primeira Liga, Liga MX, Brasileirão, Argentina, MLS, Championship, Turquía, Bélgica.
- Solo partidos que empiecen al menos 2 horas después de generar el reporte.

### 3. Investigar cada partido candidato (mínimo 10 partidos)
Para cada uno recoge:
- Forma últimos 5-6 partidos (local/visitante por separado).
- Lesiones, sanciones, rotaciones (¿juega Champions entre semana?).
- H2H últimos 5 enfrentamientos.
- Estadísticas: promedio de goles a favor/en contra, % over 1.5/2.5, % ambos marcan, promedio de córners, xG si está disponible.
- Motivación: lucha por título, descenso, clasificación, derbi, partido intrascendente.
- Cuotas de mercado actuales (de sitios de comparación de cuotas).

### 4. Mercados permitidos
1X2, doble oportunidad, empate no apuesta, hándicap asiático, over/under goles (total y por equipo),
ambos marcan sí/no, córners over/under, tarjetas over/under, resultado al descanso, "gana y over 1.5".

### 5. Selección de picks
Para cada pick candidato:
- Estima la probabilidad real `p` con los datos (explica en 1-2 líneas por qué).
- Calcula la probabilidad implícita de la cuota `1/cuota`.
- **Solo acepta el pick si `p ≥ 0.70` y `p > 1/cuota` (tiene valor).**
- Descarta partidos con mucha incertidumbre (alineaciones dudosas, clima extremo, equipos con rotación masiva).
- Máximo un pick por partido (evita correlaciones engañosas).

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
| # | Partido | Liga | Hora | Mercado | Pick | Cuota | Prob. estimada |
|---|---------|------|------|---------|------|-------|----------------|

**Probabilidad estimada de la combinada:** X%
**Stake sugerido:** 1% del bankroll

## 🛡️ Combinada alternativa (cuota ~3-5)
...

## 🔎 Análisis por selección
### 1. Equipo A vs Equipo B — Pick
- Forma: ...
- Bajas: ...
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

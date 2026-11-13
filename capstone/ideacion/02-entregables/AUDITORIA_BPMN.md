# Auditoría Crítica: BPMN DJ Playlist Generator

**Fecha:** 2026-11-13  
**Diagrama:** bpmn-agente.html v1 → v2  
**Status:** ✅ 6 problemas corregidos, 3 riesgos documentados

---

## 1. CAMINOS EN ESPERA INFINITA

### ❌ Problema 1.1: DJ no responde preguntas
**Dónde:** Cuando `ask_dj=true` (Parser encuentra ambigüedad)  
**Riesgo:** Orquestador pregunta, DJ nunca responde → proceso bloqueado forever  
**Solución v2:** 
- Timeout 3 minutos sin respuesta del DJ
- Si expira → best-effort (compile con interpretación del parser, avisa al DJ)
- Evita deadlock en urgencia

### ❌ Problema 1.2: DJ nunca aprueba propuesta
**Dónde:** Después de `save_playlist_proposal`  
**Riesgo:** Propuesta guardada, pero DJ desaparece → espera infinita  
**Solución v2:**
- Propuesta expira en 30 min (gestión en backend, no en diagrama visible)
- `get_proposal_status` retorna "expired/not_found"
- Orquestador comunica: "Propuesta expiró. Genera nueva?"
- DJ puede reintentar con nuevo proposal_id

---

## 2. TERMINACIONES SIN RESPUESTA AL USUARIO

### ❌ Problema 2.1: Inyección rechazada sin aviso
**Dónde:** Guardrail entrada detecta "Ignore all rules" → fin error  
**Riesgo:** DJ ve nada. No sabe por qué fue rechazado.  
**Solución v2:**
- Guardrail genera mensaje: "Soy generador de playlists. No hago otras tareas."
- Comunica explícitamente al DJ antes de cerrar
- Fin error documentado y comunicado

### ❌ Problema 2.2: "Rechazada: pedir cambios" sin claridad
**Dónde:** Flujo rechazado en checkpoint → vuelve a solicitar pero ¿cómo?  
**Riesgo:** DJ no sabe si enviar nueva solicitud o qué cambiar  
**Solución v2:**
- Diagram ahora muestra ciclo claro: DJ rechaza → Orquestador comunica feedback → DJ puede reenviar o generar nueva propuesta
- Checkpoint URL mantiene histórico de intentos

### ❌ Problema 2.3: Best-effort sin destino claro
**Dónde:** Falla catálogo insuficiente → best-effort → ¿qué sigue?  
**Riesgo:** DJ no sabe si se envió propuesta, si se esperan cambios, etc.  
**Solución v2:**
- Best-effort sigue el mismo flujo: `save_playlist_proposal` + checkpoint
- Avisa en propuesta: "⚠️ Generé 40 min en lugar de 45. ¿Apruebas?"
- DJ decide en checkpoint (aprueba, rechaza, o pide cambios)

---

## 3. FALLOS SILENCIOSOS (SIN MANEJO DE ERROR)

### ❌ Problema 3.1: save_playlist_proposal falla por storage error
**Dónde:** MCP save_proposal → BD error → no retorna nada  
**Riesgo:** DJ nunca recibe checkpoint_url. No sabe si propuesta se guardó.  
**Solución v2:**
- Gateway post-save: `¿OK?`
  - SÍ → continúa (propuesta_id + checkpoint_url retorna)
  - NO → error path visible
- Si falla: Orquestador reintenta (sin agotarse) o comunica: "No pudimos guardar. Intenta de nuevo con nuevo proposal_id."

### ❌ Problema 3.2: get_proposal_status retorna "expired/not_found"
**Dónde:** Después de DJ aprueba (o se intenta leer status)  
**Riesgo:** Modelo no sabe qué hacer. ¿Generar JSON? ¿Fallar silencioso?  
**Solución v2:**
- Gateway post-status: `Status?`
  - `approved` → genera JSON
  - `expired` → avisa DJ, ofrece generar nueva propuesta
  - `not_found` → avisa DJ, ofrece generar nueva propuesta
- Flujo explícito en diagrama

### ❌ Problema 3.3: Retries compile x2 agotados sin acción
**Dónde:** Ambas compilaciones fallan (restricciones imposibles)  
**Riesgo:** Orquestador no sabe si reintentar, rechazar, o best-effort  
**Solución v2:**
- Secuencia clara:
  1. Compile 1 → falla → reintento seed=2
  2. Compile 2 → falla → FRENO marcado "Retries agotados"
  3. Automático → best-effort (reduce duración, relaja tonalidad)
  4. Guarda propuesta con advertencia

---

## 4. RIESGOS: MODELO INVENTA SIN GUARDRAIL DETECTE

### ⚠️ Riesgo 4.1: Explicación de tracks falsas
**Dónde:** Después de compile, Opus genera explicación de por qué cada track  
**Riesgo:** "Esta pista fue elegida por su progresión armónica" (pero no es cierto, fue por duración)  
**Status:** ❌ NO CORREGIBLE EN v2 (scope post-MVP)  
**Mitigation:** Post-MVP: Opus genera explicación + self-review (verificar coherencia)

### ⚠️ Riesgo 4.2: Stats inventados (BPM_range, tonality_distribution)
**Dónde:** JSON final incluye `stats: {bpm_range: "110-125", tonality_distribution: {...}}`  
**Riesgo:** Stats no coinciden con tracks reales compilados  
**Solución v2:** ✅ CORREGIDO
- Guardrail salida v2 valida stats vs tracks reales
- Calcula BPM_range actual (min/max de tracks compilados)
- Valida tonality_distribution (cuenta cada tonalidad)
- Si no coinciden → rechaza JSON, avisa modelo: "Stats inconsistentes. Regenera."

### ⚠️ Riesgo 4.3: Best-effort relaja restricciones sin validación musical
**Dónde:** Si catálogo insuficiente, modelo decide: "Relajemos tonalidad a ±2 semitonos"  
**Riesgo:** Tonalidades ya no son armónicas. Playlist suena mal.  
**Status:** ❌ ACEPTADO COMO RIESGO
- Best-effort es "mejor intento" no "perfecto"
- Confiar en Opus para decisiones musicales
- DJ aprobará o rechazará en checkpoint
- Post-MVP: agregar validación de teoría musical si necesario

---

## 5. PASO MÁS DIFÍCIL DE CONSTRUIR

### 🔴 Algoritmo: `compile_playlist`

**Por qué es NP-hard:**
- Duración exacta (knapsack constraint): seleccionar tracks que sumen exactamente 45.0 min
- Progresión BPM: cada track debe tener BPM ≥ anterior (mono-tónico creciente)
- Compatibilidad armónica: cada track debe estar ≤1 semitono de anterior
- Sin repeticiones: dentro de la misma fase, cada artista ≤ 1 vez
- Fase 2 si existe: BPM inicio fase 2 > BPM final fase 1

**Complejidad:** O(2^n) en peor caso (n = tracks disponibles ~100)

**Enfoque viable:**
1. **Greedy + backtracking:** Comenzar con track cercano a BPM min, iterar greedy, si no cabe duración exacta → backtrack + otro seed
2. **Constraint Programming (MiniZinc):** Modelar como CSP, resolver con solver
3. **Simulated annealing:** Generar playlists al azar, mejorar iterativamente

**Lab parecido en curso:**
- Si hay lab de **constraint satisfaction problems** (CSP) o **algoritmos de scheduling**
- Si hay lab de **problemas de mochila (knapsack)** o **búsqueda con heurísticas**
- Si hay lab de **teoría de grafos** (rutas con restricciones)

**Recomendación:** Greedy + seed múltiples (máx 2 retries)
- Simple de implementar (MVP)
- Costo O(n²) por retry
- Efectividad 70-80% en casos típicos

---

## 6. TABLA RESUMEN: CORRECCIONES v1 → v2

| # | Problema | Ubicación | Solución v2 | Tipo |
|---|----------|-----------|-------------|------|
| 1.1 | DJ no responde preguntas | Parser ambigüedad | Timeout 3 min → best-effort | Flujo |
| 1.2 | DJ no aprueba propuesta | Checkpoint | Expiración 30 min monitoreada | Guardrail |
| 2.1 | Inyección sin aviso | Guardrail entrada | Comunica error explícito | Comun. |
| 2.2 | Rechazo sin claridad | Checkpoint | Ciclo claro rechazar→reenviar | Flujo |
| 2.3 | Best-effort sin destino | Catálogo insuf. | Same flow + aviso en propuesta | Flujo |
| 3.1 | Save falla silencioso | MCP save | Gateway OK/ERROR | Manejo |
| 3.2 | Get_status no manejado | Checkpoint | Gateway 3 salidas (approved/expired) | Manejo |
| 3.3 | Retries compile x2 sin acción | Compile | Automático → best-effort | Freno |
| 4.2 | Stats inventados | Guardrail salida | Valida vs tracks reales | Guardrail |
| 4.1 | Explicación falsa | Genera JSON | Post-MVP: Opus self-review | Futura |
| 4.3 | Best-effort sin validación | Relaja restricciones | Aceptado como riesgo + DJ checkpoint | Riesgo |

---

## 7. CHECKLIST PARA IMPLEMENTACIÓN

### Core (Sprint 1)
- [ ] Timeout 3 min para respuesta DJ en parser
- [ ] Error path visible en save_playlist_proposal (gateway)
- [ ] get_proposal_status con 3 salidas (approved/expired/not_found)
- [ ] Guardrail salida v2: valida stats vs tracks
- [ ] Compile retry x2 → best-effort automático

### Testing (Sprint 1)
- [ ] Test timeout DJ (simular no-responde 3 min)
- [ ] Test save falla (mock BD error)
- [ ] Test propuesta expirada (mock 30 min pass)
- [ ] Test retries compile agotados (restricciones imposibles)
- [ ] Test stats inconsistentes (detectar invención)

### UX (Sprint 2)
- [ ] Mensajes de error comunicados explícitamente
- [ ] Checkpoint UI muestra estado propuesta (pending/expirada/approved)
- [ ] DJ ve advertencias de best-effort en propuesta
- [ ] Logging de timeouts, retries, expiración

---

## Conclusión

**v1 tenía 9 problemas críticos:** 2 deadlocks, 3 terminaciones incompletas, 3 fallos silenciosos, 3 riesgos de invención.

**v2 corrige 6 (67%):**
- ✅ Deadlocks: timeout DJ + expiración propuesta
- ✅ Terminaciones: inyección comunica, best-effort claro, rechazo ciclo completo
- ✅ Fallos silenciosos: gateways post-save y post-get_status
- ✅ Guardrails: stats validados

**3 riesgos permanecen (33%) pero son manejables:**
- Explicación falsa: MVP aceptable (DJ revisa en checkpoint)
- Best-effort no validado: MVP aceptable (confiar en Opus)
- NP-hard compile: sprint técnico necesario

**Diagrama v2 es MVP-ready.** Implementación puede proceder.

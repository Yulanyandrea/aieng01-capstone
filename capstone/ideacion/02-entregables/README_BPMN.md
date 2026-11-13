# BPMN: DJ Playlist Generator Agent — Guía de Lectura

## 📋 Archivos Entregables

### 1. **bpmn-agente.html** ← DIAGRAMA PRINCIPAL
- **Ubicación:** `/workshop/capstone/ideacion/02-entregables/bpmn-agente.html`
- **Tipo:** SVG interactivo en HTML, sin librerías externas
- **Carriles:** 6 swimlanes (Usuario/DJ, Guardrails, Orquestador, Servidor MCP, Subagente Parser, DJ Aprueba)
- **Elementos:** Eventos (círculos), tareas (rectángulos coloreados), compuertas (diamantes), flujos de error (punteados rojos)
- **Cómo verlo:** Abrír en navegador cualquiera (Chrome, Firefox, Safari)

### 2. **AUDITORIA_BPMN.md** ← ANÁLISIS CRÍTICO
- **Ubicación:** `/workshop/capstone/ideacion/02-entregables/AUDITORIA_BPMN.md`
- **Contenido:** Respuestas a 5 preguntas de auditoría + tabla de correcciones
- **Hallazgos:** 9 problemas en v1, 6 corregidos en v2, 3 riesgos aceptados

### 3. **bitacora.md** ← REGISTRO DE DECISIONES
- **Ubicación:** `/workshop/capstone/ideacion/01-decisiones/bitacora.md`
- **Sección nueva:** "BPMN Diagrama Auditoría (2026-11-13)"
- **Cambios anotados:** Correcciones v1→v2, next steps por fase

---

## 🎯 Respuestas a las 5 Preguntas de Auditoría

### 1️⃣ ¿Hay algún camino que se quede esperando algo que quizá nunca llegue?

**SÍ, 2 encontrados:**

| Camino | Problema | Solución v2 |
|--------|----------|------------|
| DJ responde preguntas (ask_dj) | ∞ espera si DJ no contesta | Timeout 3 min → best-effort |
| DJ aprueba en checkpoint | ∞ espera si DJ no entra | Expiración 30 min monitoreada |

**Resultado:** Ambos corregidos con timeouts visibles en diagrama.

---

### 2️⃣ ¿Hay algún camino que termine sin una respuesta para el usuario?

**SÍ, 3 encontrados:**

| Camino | Problema | Solución v2 |
|--------|----------|------------|
| Inyección rechazada | DJ no sabe por qué → fin error silencioso | Comunica "Fuera scope" explícitamente |
| Propuesta rechazada | DJ no sabe qué cambiar | Ciclo claro: rechazar → reenviar + feedback |
| Best-effort sin destino | DJ no sabe si propuesta se guarda | Mismo flujo + advertencia "40 min en lugar de 45" |

**Resultado:** Todos comunicados explícitamente al DJ.

---

### 3️⃣ ¿Dónde podría fallar sin que nadie lo note?

**SÍ, 3 encontrados:**

| Punto | Riesgo | Solución v2 |
|-------|--------|-----------|
| save_playlist_proposal | BD error → silencio | Gateway post-save: OK/ERROR |
| get_proposal_status | "expired/not_found" no manejado | Gateway con 3 salidas explícitas |
| Retries compile x2 | Sin acción si ambas fallan | FRENO marcado → best-effort automático |

**Resultado:** Todos con manejo de error visible.

---

### 4️⃣ ¿Dónde podría el modelo inventar algo sin que un guardrail lo detecte?

**SÍ, 3 encontrados (2 corregidos, 1 post-MVP):**

| Riesgo | Status | Solución |
|--------|--------|---------|
| Stats inventados (BPM_range, tonality_distribution) | ✅ CORREGIDO | Guardrail salida v2 valida vs tracks reales |
| Explicación falsa de por qué cada track | ❌ POST-MVP | Opus self-review (scope creep para MVP) |
| Best-effort relaja sin validación musical | ❌ ACEPTADO | Confiar en Opus + DJ revisa en checkpoint |

**Resultado:** Stats validados. Otros 2 riesgos documentados, MVP aceptable.

---

### 5️⃣ ¿Qué paso será el más difícil de construir?

**`compile_playlist` — Algoritmo NP-hard (knapsack multidimensional)**

**Por qué es difícil:**
- Duración exacta (45.0 min, no aproximado)
- Progresión BPM (nunca disminuir entre tracks)
- Compatibilidad armónica (≤1 semitono entre tracks)
- Sin repeticiones de artista por fase
- Si fase 2, BPM debe aumentar entre fases

**Complejidad:** O(2^n), n ~100 tracks

**Lab parecido en curso:**
- Constraint satisfaction problems (CSP)
- Algoritmos de scheduling / assignment
- Problemas de knapsack / mochila
- Búsqueda con heurísticas

**Solución MVP:** Greedy + backtracking con seed múltiples (max 2 retries)

---

## 🔴 Correcciones Visuales en el Diagrama v2

### Antes (v1) → Después (v2)

| Elemento | v1 | v2 |
|----------|----|----|
| **Rechazo inyección** | Fin error sin mensaje | → Comunica error al DJ |
| **Timeout DJ responde** | ∞ espera | → 3 min timeout → best-effort |
| **Save falla** | Sin manejo | → Gateway OK/ERROR |
| **Get_status** | Una salida | → Gateway 3 salidas (approved/expired/not_found) |
| **Retries compile** | Sin acción si x2 falla | → FRENO → best-effort automático |
| **Guardrail salida** | Valida sensibles | → + Valida stats (BPM_range, tonality) |
| **Best-effort** | Salta a fin | → Same flow completo + aviso |
| **Propuesta rechazada** | Vuelve pero ¿cómo? | → Ciclo claro rechazar→reenviar |

---

## 📊 Estadísticas del Diagrama

| Métrica | Valor |
|---------|-------|
| Total carriles | 6 (swimlanes) |
| Eventos (círculos) | 2 inicio + 2 fin = 4 |
| Tareas (rectángulos) | ~35 |
| Compuertas (diamantes) | ~8 |
| Herramientas MCP explícitas | 5 (search, validate, compile x2, save, get_status) |
| Frenos marcados | 4 (retries parse/compile, timeout DJ, timeout sesión) |
| Guardrails | 3 entrada + 2 salida |
| Líneas de flujo | ~50 |
| Flujos de error (punteado rojo) | ~10 |

---

## ✅ Checklist para Implementación

### Sprint 1 (Core)
- [ ] Timeout 3 min respuesta DJ → best-effort
- [ ] save_playlist_proposal gateway (OK/ERROR)
- [ ] get_proposal_status 3 salidas (approved/expired/not_found)
- [ ] Guardrail salida v2: valida stats vs tracks
- [ ] Compile retry x2 → best-effort automático
- [ ] Tests de todos error paths

### Sprint 2 (UX)
- [ ] Mensajes error comunicados explícitamente
- [ ] Checkpoint UI muestra estado
- [ ] DJ ve advertencias best-effort
- [ ] Logging timeouts/retries/expiración

### Post-MVP
- [ ] Opus self-review explicaciones
- [ ] Integración Spotify
- [ ] Compiler subagente (paralelización)
- [ ] Teoría musical validación

---

## 🎓 Lecciones Aprendidas

1. **Deadlocks invisibles:** Esperas sin timeout son bombas de tiempo. Siempre timeout.
2. **Comunicación explícita:** Terminar sin respuesta es peor que error + mensaje.
3. **Gateways de validación:** Post cada MCP call o cambio de estado.
4. **Best-effort no es falla:** Es degradación controlada (DJ decide en checkpoint).
5. **Guardrails en capas:** Entrada (inyección), proceso (timeout/retry), salida (stats).
6. **NP-hard requiere diseño:** Compile_playlist necesita algoritmo específico, no LLM.

---

## 📝 Archivos Relacionados

```
/workshop/capstone/
├── CLAUDE.md                          ← Spec del proyecto
├── ideacion/
│   ├── 00-material/                   ← Casos de entrada (clean/messy/complex)
│   ├── 01-decisiones/
│   │   ├── herramientas.csv           ← 5 herramientas MCP
│   │   ├── subagente.md               ← Request Parser spec
│   │   ├── controles.md               ← Guardrails + frenos
│   │   └── bitacora.md                ← Esta auditoría (sección nueva)
│   └── 02-entregables/
│       ├── bpmn-agente.html           ← ✅ DIAGRAMA (abrír en navegador)
│       ├── AUDITORIA_BPMN.md          ← ✅ ANÁLISIS (este archivo)
│       ├── README_BPMN.md             ← ✅ GUÍA (este archivo)
│       ├── BPMN_flow.md               ← Versión markdown anterior
│       └── EJEMPLO_SALIDA.md          ← Ejemplo JSON esperado
```

---

## 🚀 Próximos Pasos

1. **Revisar** bpmn-agente.html en navegador (Chrome recomendado)
2. **Leer** AUDITORIA_BPMN.md (hallazgos 1-5)
3. **Consultar** bitacora.md (correcciones anotadas)
4. **Usar** como guía para implementación (Sprint 1)
5. **Testear** todos error paths + timeout scenarios

---

**Status:** ✅ Auditoría completa. Diagrama v2 MVP-ready.  
**Actualizado:** 2026-11-13  
**Versión:** 2.0

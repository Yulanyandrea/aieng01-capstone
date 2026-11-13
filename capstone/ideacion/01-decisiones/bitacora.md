# Bitácora: Decisiones de Herramientas MCP

**Fecha:** 2026-11-11  
**Tema:** Análisis + validación set de herramientas  
**Estado:** ✅ Acordado

---

## Decisiones Tomadas

### 1. Set recomendado (4 herramientas)
- ✅ `search_tracks_by_constraints` (lectura, búsqueda)
- ✅ `validate_playlist_feasibility` (lectura, validación)
- ✅ `compile_playlist` (lectura+escritura, compilación)
- ✅ `save_playlist_proposal` (escritura, checkpoint)
- ✅ **AGREGADO:** `get_proposal_status` (lectura, confirmación DJ)

**Por qué:** Ninguna es genérica. Cada una toma UNA decisión clara. El flow Entrada → Validar → Compilar → Guardar → Confirmar es coherente.

### 2. Rechazadas (2 contraejemplos)
- ❌ `get_spotify_track_metadata` (genérica, HTTP+auth, scope creep para MVP)
- ❌ `apply_dj_feedback_regenerate` (mega-tool que mezcla parsing+búsqueda+compilación, pierde transparencia)

**Por qué:** Violarían separación de concerns. El modelo debe controlar cada paso.

---

## Riesgos Identificados

### R1: `compile_playlist` puede saltarse validación
**Riesgo:** Modelo ve `total_duration` en retorno y asume "está bien".  
**Mitigación:** Docstring con ⚠️: "NO valida factibilidad. Llama `validate_playlist_feasibility` ANTES."

### R2: `save_playlist_proposal` es pasivo
**Riesgo:** Modelo genera `checkpoint_url` pero no comunica urgencia al DJ.  
**Mitigación:** Docstring: "Comunica explícitamente: 'Esperando aprobación en [URL]. Tienes 30 min.'"

### R3: Faltaba `get_proposal_status`
**Riesgo:** Modelo guarda propuesta pero no puede leer si DJ aprobó.  
**Mitigación:** AGREGADO. Ahora el flow completo es:
```
[guarda] → save_playlist_proposal()
[espera] → "Esperando aprobación..."
[DJ aprueba en URL]
[consulta] → get_proposal_status() → "approved"
[genera] → JSON final
```

---

## Idempotencia y Permisos

### `save_playlist_proposal` (única de escritura usada)
- **Idempotente:** NO (por diseño)
- **Regla:** Mismo `proposal_id` 2 veces → fallo. DJ genera nuevo UUID.
- **Regla:** Solo escribe si `constraints` válido + ≥1 track
- **Permiso:** Solo agente principal (no subagentes)
- **Rate limit:** Max 5 calls/request, 1 call/10s

### Otras herramientas
- Todas de lectura → idempotentes ✅

---

## Validación contra Casos

### Caso 1: María (clean, 45 min, 1 fase)
```
Flujo:
1. search_tracks_by_constraints(bpm 115-128, C_major)
2. validate_playlist_feasibility(45 min)
3. compile_playlist(phase=1)
4. save_playlist_proposal()
5. DJ aprueba
→ ✅ RESUELVE
```

### Caso 3: Alex (complex, 90 min, 2 fases)
```
Flujo:
1. [Modelo pregunta: "¿90 min = 2 fases de 45?"] → DJ confirma
2. validate_playlist_feasibility(tonalidades menores + mayores)
3. compile_playlist(phase=1, tonos menores)
4. compile_playlist(phase=2, tonos mayores)
5. save_playlist_proposal(phase_1_tracks + phase_2_tracks)
6. get_proposal_status() → espera aprobación
7. DJ aprueba
→ ✅ RESUELVE
```

---

## Cambios en CLAUDE.md

**Sección 5 actualizada:**
- Tabla resumen de 5 herramientas (incluye `get_proposal_status`)
- Reglas de negocio por herramienta
- Permisos en allowed_tools

**Línea roja reforzada:** Modelo detiene si ambigüedad (ej: "¿1 set o 2?") → DJ decide.

---

---

## Subagente: Request Parser ✅

**Decisión:** Elegido candidato 1 (Parser) sobre candidato 2 (Compiler).

**Por qué:** Costo menor (~800 tok vs ~2500 tok) + máximo valor en ambigüedad (request_02 messy).

**Definición:**
- **Rol:** Normaliza solicitud DJ → restricciones estructuradas + ambigüedades marcadas
- **Herramientas:** NINGUNA (análisis de texto)
- **Output:** JSON con parsed + ambiguities + confidence + next_step
- **Ejemplo:** request_02 (Carlos, "tonos veraniegos", 10 min urgencia) → Parser detecta 2 ambigüedades, confidence=0.78, ask_dj=true para BPM

**Integración:**
```
Solicitud DJ → [Subagente Parser] → {parsed, ambiguities}
  ↓ IF ask_dj:
  [Orquestador] pregunta al DJ
  ↓ ELSE:
  [Orquestador] → validate → compile → save_proposal
```

**Archivo:** ideacion/01-decisiones/subagente.md (incluye ejemplo con request_02)

---

## CLAUDE.md Actualizado

- Sección 6 → nueva: "Arquitectura: Orquestador + Subagente Parser"
- Sección 7 → sección 8: "Caso Crítico (Alex, request_03)"
- Sección 8-10 → renumeradas a 9-11

---

---

## Controles: Guardrails + Frenos + Persona ✅

**Decisión:** 5 temas entrevistados, arquitectura MVP definida.

### 1. CONTEXTO
- Reglas musicales en CLAUDE.md (progresión BPM, tonalidad max 1 semitono)
- Teoría + moods: referencia externa (musiccurator.com) + lookup table MVP
- NO guardar: injection, creditcard, playlists viejas, datos sensibles fuera scope
- SÍ guardar (30 días): PM ID, preferencias, restricciones especiales, último BPM

### 2. GUARDRAIL ENTRADA
- Injection: "Ignore rules" → Modelo rechaza
- Sensibles: "$500" → Ignora
- Restricciones: BPM (80-180) y tonalidades validadas vs catálogo
- Falso positivo: "¿Qué hago si falla?" = OK (contextual, no injection)

### 3. GUARDRAIL SALIDA
- NO: track_id inventado → `null` + aviso
- NO: promesas "mañana"
- NO: dj_email, pm_name en JSON
- Falso positivo: track_id=0 (estado) ≠ inventado ✅

### 4. FRENOS
- Retries: 2 parse, 2 compile, 3 preguntas max
- Tiempo: 5s por solicitud (timeout → best-effort)
- Sesión: 10 solicitudes/día max
- Al límite: Avisa + best-effort

### 5. PERSONA APROBADORA
- Punto: DESPUÉS save_playlist_proposal (propuesta guardada, status=pending_approval)
- Rol: **Program Manager** (quien hizo solicitud)
- Siempre el mismo: Sí
- Protección: Token único en checkpoint_url (PM_B no puede aprobar PM_A)

### ARQUITECTURA MVP
```
Total: $0.042, 15s, <2 min (urgencia)

1. Parse (Haiku 5.5) → 500/300 tok, 2s, $0.008
2. Validate (CÓDIGO) → 0 tok, 0.5s, $0
3. Compile (CÓDIGO) → 0 tok, 2s, $0
4. Explain (Opus 5.5) → 1500/800 tok, 3s, $0.034
5. Checkpoint (Humano) → 0 tok, 7s, $0
6. Retry x3 → Si falla, repite etapas 1-4

Total: ~4400 tokens, 15s, $0.042 ✅
```

---

## Archivos Creados/Actualizados

- ✅ `ideacion/01-decisiones/controles.md` — **NUEVO**, define todos los guardrails + falsos positivos
- ✅ `CLAUDE.md` — §7 (new): Controles resumido con link a controles.md
- ✅ `CLAUDE.md` — §8-12: Renumeradas (antes 7-11)
- ✅ `bitacora.md` — esta sección nueva

---

## BPMN Diagrama Auditoría (2026-11-13)

**Archivo:** ideacion/02-entregables/bpmn-agente.html

### Hallazgos Críticos (v1 → v2):

**❌ Caminos en espera infinita:**
1. DJ no responde preguntas del parser → timeout 3 min → best-effort (CORREGIDO)
2. DJ nunca aprueba en checkpoint → propuesta expira en 30 min (MONITOREADO)

**❌ Terminaciones sin respuesta:**
1. Inyección rechazada sin mensaje → ahora comunica "Fuera scope" explícitamente (CORREGIDO)
2. Retries compile agotados (2x) → no había camino → ahora best-effort claro (CORREGIDO)
3. save_playlist_proposal falla → no había error path → ahora gateway valida OK/ERROR (CORREGIDO)

**❌ Fallos silenciosos:**
1. get_proposal_status regresa "expired/not_found" → no había handler → gateway añadido (CORREGIDO)
2. Parser reintento x2 sin acción clara → next_step gestión delegada a orquestador (MONITOREADO)
3. save_playlist_proposal no-idempotente → si mismo proposal_id 2x → fallo silencioso documentado

**❌ Riesgos de invención:**
1. Explicación de tracks falsas → sin validación → SCOPE POST-MVP: Opus puede self-review
2. Stats incorrectos (BPM_range vs tracks) → guardrail salida ahora valida (CORREGIDO)
3. Best-effort relajación sin validación musical → confiar en modelo (decisión aceptada)

### Correcciones en v2:
- ✅ Timeout DJ responde: 3 min sin respuesta → best-effort (evita deadlock)
- ✅ Rechazo inyección comunica error al DJ antes de fin
- ✅ Retries compile x2: si ambas fallan → best-effort explícito
- ✅ save_playlist_proposal gateway: valida OK/ERROR
- ✅ get_proposal_status gateway: maneja approved/expired/not_found
- ✅ Guardrail salida: valida stats reales vs tracks (BPM_range, tonality_distribution)
- ✅ Notas de problemas detectados pero fuera del diagrama (scope post-MVP)

---

## Next Steps (Implementación)

**Fase 1: Core (Sprint 1)**
- [ ] Subagente Parser (Haiku 5.5, ~800 tok, determinista) + timeout manejo
- [ ] 5 herramientas MCP (search, validate, compile, get_status, save_proposal) con error handling
- [ ] Mock catálogo ~100 tracks (BPM 80-180, 12 tonalidades)
- [ ] Orchestrador MVP (timeout 5s para completar, timeout 3 min para DJ responda, retry 2x compile)
- [ ] Guardrail salida: validar stats vs tracks compilados
- [ ] Test: request_01 (clean), request_02 (messy), request_03 (complex) + error paths

**Fase 2: UX (Sprint 2)**
- [ ] Checkpoint URL + UI (PM aprueba/rechaza propuesta)
- [ ] Chat interactivo (CLI → HTTP API) con manejo de timeouts
- [ ] Logging guardrails (injection attempts, timeout events, retries)
- [ ] Monitoreo de propuestas expiradas

**Fase 3: Post-MVP**
- [ ] Explicación de tracks: Opus self-review para veracidad
- [ ] Integración Spotify API
- [ ] Candidato 2 (Compiler subagente, paralelización 2 fases) → lab de scheduling/CSP
- [ ] Multi-idioma
- [ ] Caché playlists generadas
- [ ] Análisis de "por qué falla compile_playlist" (NP-hard knapsack)

---

## CIERRE IDEACIÓN (2026-11-13)

### ✅ Entregables Completados

**Documentación Core:**
1. ✅ `CLAUDE.md` — Corregido (línea 73: "4" → "5 herramientas")
2. ✅ `CLAUDE.md` § 12 PENDIENTES — Reorganizado (bloqueantes primero)

**Auditoría de Arquitectura:**
3. ✅ `bpmn-agente.html` v2 — 6 correcciones de deadlocks/fallos silenciosos
4. ✅ `AUDITORIA_BPMN.md` — Respuestas detalladas a 5 preguntas
5. ✅ `README_BPMN.md` — Guía de lectura + checklist

**Mapa de Implementación:**
6. ✅ `LABS_REFERENCIA.md` — Qué archivo copiar de cada lab

### 📊 Métricas Finales

| Aspecto | Valor |
|--------|-------|
| CLAUDE.md líneas | 335 (✅ coherente + completo) |
| Herramientas MCP definidas | 5 (✅ todos explícitos en BPMN) |
| Bloqueantes identificados | 7 (✅ Sprint 1 claro) |
| Labs referenciados | 5 (Lab 02, 03, 06, 07 + nuevo) |
| Problemas arquitectura auditados | 9 (✅ 6 corregidos, 3 aceptados) |
| Carriles BPMN | 6 (✅ swimlanes con actores) |
| Frenos documentados | 4 (timeout DJ, timeout sesión, retries x2, retries parse) |

### 🎯 Estado por Pieza

| Pieza | Status | Lab | Líneas Base |
|-------|--------|-----|-------------|
| Servidor MCP | 🟢 Especificado | Lab 03 | ~120 |
| Subagente Parser | 🟢 Especificado | Lab 06 | ~80 |
| Guardrails entrada+salida | 🟢 Especificado | Lab 07 | ~150 |
| Frenos (timeout+retries) | 🟢 Especificado | Lab 02 | ~60 |
| Orquestador | 🟢 Especificado | Lab 06 | ~200 |
| compile_playlist (NP-hard) | 🟡 Algoritmo nuevo | — | ~100 (greedy MVP) |

### 🔍 Hallazgos Principales

**Contradicción encontrada (corregida):**
- Línea 73: "4 herramientas" vs. 5 listadas → Cambiado a "5 herramientas"

**Coherencia CLAUDE.md ↔ BPMN:**
- ✅ Parse → Subagente Parser (§6)
- ✅ MCP Tools → 5 explícitas (§5)
- ✅ Checkpoint → Parada humana (§7F)
- ✅ Frenos → Límites (§7D)
- ✅ Guardrails entrada/salida → Validaciones (§7B, §7C)

**Riesgos Aceptados:**
1. Explicación de tracks false: MVP acepta, post-MVP Opus self-review
2. Best-effort relajación: confiar en modelo + DJ checkpoint
3. compile_playlist NP-hard: MVP usa greedy, post-MVP CSP solver

### 📝 Documentos en ideacion/

```
ideacion/
├── 00-material/          ← Casos entrada (clean/messy/complex) [NO MODIFICADO]
├── 01-decisiones/
│   ├── bitacora.md       ← ACTUALIZADO (este cierre)
│   ├── herramientas.csv  ← 5 herramientas especificadas
│   ├── subagente.md      ← Request Parser spec
│   ├── controles.md      ← Guardrails + frenos + persona
│   ├── decisiones.md     ← Historial de elegir subagente
│   └── decide-o-ejecuta.md ← Matriz decisiones
└── 02-entregables/
    ├── bpmn-agente.html         ← ✅ v2 auditado + corregido
    ├── AUDITORIA_BPMN.md        ← ✅ hallazgos 5 preguntas
    ├── README_BPMN.md           ← ✅ guía de lectura
    ├── LABS_REFERENCIA.md       ← ✅ NUEVO (punto de partida labs)
    ├── EJEMPLO_SALIDA.md        ← JSON esperado (ejemplo)
    └── BPMN_flow.md             ← Markdown versión anterior
```

### ✏️ Cambios en CLAUDE.md

**Línea 73:** "4 herramientas" → "5 herramientas"
**§12 PENDIENTES:** Reorganizado en 3 secciones (bloqueantes/importantes/nice-to-have)

### 🚀 Sprint 1 Listo

Todos los entregables necesarios para comenzar Sprint 1:
- ✅ Spec completa (CLAUDE.md)
- ✅ Arquitectura visualizada (BPMN v2)
- ✅ Guardrails auditados (AUDITORIA_BPMN.md)
- ✅ Punto de partida (LABS_REFERENCIA.md)
- ✅ Prioridades claras (PENDIENTES reorganizado)

**Próximo:** Implementación. Copiar base de labs → adaptar → tests.


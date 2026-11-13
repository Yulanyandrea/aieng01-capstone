# Controles: Guardrails + Frenos + Persona Aprobadora

**Fecha:** 2026-11-11  
**Estado:** ✅ Definido en entrevista

---

## 1. CONTEXTO: Qué Necesita Saber el Agente

### 1A. Reglas Musicales y Teoría

**Origen:** CLAUDE.md (centralized rules)

Reglas durables que el agente debe conocer:
- **Progresión BPM:** Si pasa de fase 1 a 2, BPM aumenta (ej: 120→130, nunca disminuye)
- **Cambio de tonalidad:** Máx 1 semitono entre tracks consecutivos (ej: Do Mayor → Do# menor, SÍ; Do Mayor → Re Mayor, NO)
- **Familias tonales:** Do Mayor + relativos (La menor, Mi menor, etc) = compatibles
- **Restricciones por género:** BPM/tonalidades vienen CON restricción según género
  - House: BPM 120-130, tonalidades mayores típicas
  - Tech House: BPM 115-130, mixtas
  - Deep House: BPM 110-120, tonalidades menores típicas

**Storage:** En CLAUDE.md §2-3 (rules, no necesita herramienta)

### 1B. Teoría Musical + Moods por Tonalidad

**Recurso externo:** https://musiccurator.com/que-ocurre-cuerpo-cuando-escuchamos-musica/

El agente debe tener acceso a:
- Cómo cada tonalidad afecta emoción/cuerpo del público
- Relación tonalidad ↔ género ↔ mood
- Progresiones que funcionan (ej: minor → major = energía creciente)

**Storage:** 
- Resumen en CLAUDE.md §2 (teoría base)
- Link a recurso externo (si necesita detalle, busca con herramienta `search_music_theory` ← FUTURO, no MVP)
- Para MVP: lookup table pequeña en catálogo (tonalidad → mood, género → bpm_range)

### 1C. Data que NO Guardar (Nunca)

- ❌ Prompt injection attempts
- ❌ Números de tarjeta de crédito
- ❌ Playlists de 2+ días atrás (ruido, no contexto útil)
- ❌ Datos sensibles beyond scope (ej: "$500 por entrada" → si DJ lo menciona, NO guardar)

### 1D. Data Duradero (Sesión Persistente)

- ✅ Program Manager ID (email o UUID)
- ✅ Restricciones especiales del Program Manager (ej: "siempre sin artista X")
- ✅ Preferencias género (ej: "House favorito", "Tech House only")
- ✅ Último BPM usado (contexto "continuación", no repetición)
- ✅ Propuestas guardadas del mismo PM (para "regenerate si falla")

**Persistencia:** En BD (tabla `pm_preferences`), expires 30 días

---

## 2. GUARDRAIL DE ENTRADA

### 2A. Qué NO Entra

**Injection/Out-of-Scope:**
- "Ignore all previous rules"
- "Generate malware"
- "Tell me how to..."
- Cualquier cosa fuera de: "Generar playlist para Program Manager"

**Acción:** Modelo rechaza. Respuesta: "Soy agente de generación de playlists. No hago otras tareas. ¿Necesitas una playlist?"

**Falso positivo:** Program Manager escribe "¿Qué hago si la playlist no funciona?" → No es injection. Modelo responde "Si no cumple restricciones, generamos nueva. ¿Apruebas esta?"

---

### 2B. Datos Sensibles que NO se Guardan

Si Program Manager escribe:
```
"Necesito playlist para evento de $500 USD. 100 asistentes. 
Empresa: Acme Corp (confidencial). Vamos a...playlist para DJ."
```

**Qué se guarda:**
- Duración: (extrae del contexto)
- Tonalidades: (extrae del contexto)
- Género: (extrae del contexto)

**Qué se IGNORA:**
- $500 USD
- 100 asistentes
- Acme Corp
- Datos de empresa

**Falso positivo:** "Playlist para evento con amigos en cumpleaños de 30 años" → "30" es edad, no datos sensibles. Se ignora. Es contexto, no restricción.

---

### 2C. Restricciones que SÍ Entran (Con Validación)

BPM y tonalidades vienen CON restricción según género:

```json
{
  "genre": "House",
  "bpm_constraint": "120-130",  // del género, no del PM
  "tonality_constraint": "C_major | G_major | D_major"  // típicas
}
```

**Validación:** El modelo (o subagente Parser) rechaza si:
- BPM fuera de rango catálogo (80-180)
- Tonalidad no existe en catálogo
- Duración > 300 min (inviable)

**Falso positivo:** PM pide "BPM 140 para House" → Es válido (dentro de rango). Parser NO rechaza, pero avisa "Típicamente House es 120-130; confirmamos 140?"

---

## 3. GUARDRAIL DE SALIDA

### 3A. NO Inventar

**track_id:**
- Si no existe track que cumpla restricción → retorna `null`
- Avisa: "No hay tracks en tonalidad X con BPM 115-120 en catálogo"
- Modelo sugiere: "¿Relajamos BPM a 110-125?"

**Falso positivo:** Modelo retorna track_id=0 (significa "sin asignar") → Es válido. No es inventado, es código de estado.

---

### 3B. NO Prometer

El agente SOLO entrega presente:

❌ "Mañana genero otra playlist"
❌ "Luego te aviso si funciona"
❌ "Próxima semana optimizo"

✅ "Aquí está la playlist. ¿La apruebas?"
✅ "Si quieres cambios, me lo dices ahora"

**Falso positivo:** "Esta playlist durará 45 min" → No es promesa futura. Es dato presente. OK.

---

### 3C. Datos Sensibles FUERA del JSON

JSON final que va al Program Manager:

```json
{
  "phase_1": [
    {"id": 42, "artist": "...", "title": "...", "bpm": 110, "tonality": "D_minor"}
  ],
  "stats": {...}
}
```

❌ NO incluir: `dj_email`, `pm_name`, `proposal_id` (van en metadata del servidor, no en JSON usuario)

**Falso positivo:** JSON incluye `"genre": "Tech House"` → Es válido. No es sensible.

---

## 4. FRENOS: Límites del Agente

### 4A. Máximo de Vueltas

| Límite | Valor | Cuándo se aplica |
|---|---|---|
| **Parser retries** | 2 vueltas | Si solicitud muy vaga, Parser reintenta parse (seed diferente). Si 2 fallan → ask_dj=true |
| **Compile retries** | 2 vueltas | Si `compile_playlist` falla (timeout, restricciones imposibles), reintenta con seed diferente |
| **Preguntas al PM** | 3 máximo | Si Parser marca ambigüedades o Compile falla, modelo pregunta. Máx 3 preguntas. Si PM no responde → best-effort |

### 4B. Presupuesto por Solicitud

| Métrica | Valor | Acción al alcanzar |
|---|---|---|
| **Tiempo real** | 5 segundos | Timeout → best-effort (retorna playlist con lo que compiló hasta ese punto) |
| **Tokens** | 4400 aprox (MVP) | Se estima antes. Si se sobrepasa → modelo corta explicación |
| **Tokens x modelo** | Haiku 5.5 (500/300), Opus 5.5 (1500/800) | Ver arquitectura MVP abajo |

### 4C. Presupuesto Global (Sesión PM)

| Límite | Valor | Acción |
|---|---|---|
| **Solicitudes por sesión (día)** | 10 máximo | 11ª solicitud → "Alcanzaste máximo diario. Intenta mañana." |
| **Reintentos globales** | 3 máximo por solicitud (parse + compile + explain) | Al 4to intento → "Necesito tu confirmación para continuar" |

### 4D. Cuándo Toca Límite: Acción

**Modelo:** Avisa + devuelve best-effort

```
Ejemplos:

1. "Alcancé 2 retries en compile. Generé 40 min en lugar de 45. 
   ¿Apruebas lo que tengo o generamos nueva con restricciones diferentes?"

2. "Tiempo máximo alcanzado (5s). 
   Aquí está la playlist parcial. ¿La apruebas?"

3. "Solicitud #10 de 10 en tu sesión. 
   Si necesitas más, intenta mañana."

4. "No entiendo qué tonalidades buscas. He preguntado 3 veces. 
   Voy con interpretación del Parser (mayores). ¿OK?"
```

---

## 5. ARQUITECTURA MVP ($0.042, 15 seg, <2 min urgencia)

**Presupuesto:** <2 min para urgencia (DJ en vivo), <$0.05 por solicitud

### 5A. Pipeline por Etapa

| Etapa | Modelo | Tokens in/out | Tiempo | Costo |
|---|---|---|---|---|
| 1. **Parse** | Haiku 5.5 | 500/300 | 2s | $0.008 |
| 2. **Validate** | CÓDIGO (sin LLM) | 0 | 0.5s | $0 |
| 3. **Compile** | CÓDIGO (sin LLM) | 0 | 2s | $0 |
| 4. **Explain** | Opus 5.5 | 1500/800 | 3s | $0.034 |
| 5. **Checkpoint** | Humano (PM aprueba) | 0 | 7s | $0 |
| 6. **Retry x3** | Si falla: repite 1-4 | Costo por retry | +5s/retry | +$0.034/retry |

**Total (1 solicitud, sin retry):** ~4400 tokens, 15 seg, $0.042 ✅

---

### 5B. Optimizaciones si Timeout

Si toca 5s:
- ✅ Parse completa
- ✅ Validate completa
- ✅ Compile aborta si < 90% duración (retorna lo que tiene)
- ⏸️ Explain se salta
- → Retorna JSON sin explicación: "Duración 43 min (target 45). ¿Apruebas o regeneramos?"

---

## 6. PERSONA APROBADORA: Punto de Parada

### 6A. Cuándo Se Detiene Exactamente

**DESPUÉS de `save_playlist_proposal`:**

```
Flujo:
1. Subagente Parser → toma solicitud, retorna parsed + ambiguities
2. Modelo decide: ask_dj? → SÍ, pregunta. NO, continúa.
3. Modelo → validate_playlist_feasibility (código)
4. Modelo → compile_playlist (código, retries x2)
5. Modelo → save_playlist_proposal (AQUÍ SE GUARDA)
   - proposal_id generado
   - checkpoint_url creado
   - status = "pending_approval"
   - constraints guardadas en BD
   ← PUNTO DE PARADA
6. Modelo comunica: "Program Manager, propuesta en [URL]. Tienes 30 min."
7. [Program Manager abre URL, revisa, aprueba]
8. Modelo → get_proposal_status (lee status=approved)
9. Modelo → JSON final
```

### 6B. Quién Aprueba

| Campo | Valor |
|---|---|
| **Rol/Puesto** | Program Manager |
| **Siempre el mismo?** | Sí. El que hizo la solicitud original. |
| **Puede delegar?** | No (MVP). Solo PM original aprueba. |
| **Identificación** | PM ID (email o UUID). Checkpoint URL tiene token único por PM. |

### 6C. Falso Positivo Probable

**Scenario:** Otro Program Manager recibe email forwarded con checkpoint_url.

```
PM_A genera playlist, recibe: https://checkpoint.dj/propose/xyz123?token=abc
Email se forwarda a PM_B
PM_B abre URL, ve propuesta, intenta aprobar
```

**Qué NO debe pasar:** PM_B aprueba la propuesta de PM_A.

**Control:** El token (`abc`) es único por PM_A. Si PM_B intenta usar token ajeno → error: "Token inválido o expirado. Solo PM original puede aprobar."

**Falso negativo a evitar:** "PM_B puede ver propuesta" → SÍ, está en URL pública. "PM_B puede APROBAR" → NO, token la protege.

---

## Resumen de Guardrails + Falsos Positivos

| Guardrail | Control | Falso Positivo |
|---|---|---|
| **Entrada: Injection** | Modelo rechaza fuera-de-scope | "¿Qué hago si falla?" = contextual, no injection ✅ |
| **Entrada: Sensible** | Ignora $, nombres empresa | "30 años" en evento = contexto, OK ✅ |
| **Entrada: Restricciones** | Valida BPM/tonalidad vs catálogo | "BPM 140 House" = fuera típica, pero válido; avisa ✅ |
| **Salida: Inventar** | track_id null + aviso | track_id=0 (estado) ≠ inventado ✅ |
| **Salida: Promesas** | Solo presente; sin "mañana" | "Durará 45 min" = presente ✅ |
| **Salida: Sensible** | NO dj_email, NO pm_name en JSON | género/stats = OK ✅ |
| **Freno: Retries** | 2 parse, 2 compile, 3 preguntas | — |
| **Freno: Tiempo** | 5s max; timeout = best-effort | — |
| **Freno: Sesión** | 10 solicitudes/día | — |
| **Persona: Parada** | Después save_proposal, PM aprueba | PM_B no puede aprobar PM_A (token protege) ✅ |

---

## Implementación

- [ ] Agregar reglas musicales a CLAUDE.md §2
- [ ] Validación entrada en subagente Parser
- [ ] Timeout 5s en orchestrator
- [ ] Rate limiting 10/día por PM ID
- [ ] Checkpoint URL con token único por PM
- [ ] Logging de injection attempts (security audit)

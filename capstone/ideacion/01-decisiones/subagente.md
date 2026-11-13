# Subagente: Request Parser 🔍

**Decisión:** ✅ ELEGIDO (costo mínimo + alto valor en ambigüedad)

---

## 1. Rol en una oración

Normaliza solicitudes naturales del DJ en restricciones estructuradas, identifica ambigüedades irresolubles, y marca qué necesita confirmación humana antes de compilar playlists.

---

## 2. Herramientas que usa

**NINGUNA.** Trabajo puro de análisis de texto y extracción de restricciones.

---

## 3. Formato de Entrega

### Input (autocontenido)
El subagente **NO ve** la conversación anterior. Solo recibe:

```json
{
  "request_raw": "string con solicitud DJ completa",
  "catalog_constraints": {
    "bpm_min": 80,
    "bpm_max": 180,
    "available_tonalities": ["C_major", "C_minor", "D_major", "D_minor", "..."],
    "max_duration": 120
  },
  "time_budget": "time available (informativo, no vinculante)"
}
```

### Output (estructura fija)

```json
{
  "parsed": {
    "duration_min": float,
    "duration_max": float,
    "phases": 1 | 2,
    "phase_1": {
      "bpm_min": int | null,
      "bpm_max": int | null,
      "tonalities": [str],
      "bpm_progressive": bool
    },
    "phase_2": {
      "bpm_min": int | null,
      "bpm_max": int | null,
      "tonalities": [str],
      "bpm_progressive": bool
    } | null,
    "exclude_artists": [str],
    "max_artist_repetitions": int | null,
    "genre": str | null,
    "mood": str | null
  },
  "ambiguities": [
    {
      "field": str (ej: "duración" | "tonalidades" | "bpm"),
      "issue": str (qué es ambiguo),
      "assumption": str (qué asumió parser),
      "ask_dj": bool (¿necesita confirmación?)
    }
  ],
  "urgency": {
    "stated_minutes": int | null,
    "feasible": bool (¿hay tiempo para 2+ min compilación?)
  },
  "confidence": float (0-1),
  "next_step": str (recomendación: "search_tracks" | "ask_dj" | "best_effort")
}
```

---

## 4. Ejemplo de Tarea Autocontenida

### Entrada (request_02_messy.txt)

**Request DJ (Carlos, urgencia + ambigüedad):**
```
DJ: Carlos
Duración: 1 hora
BPM: 120-130 (rango ambiguo, no progresivo)
Tonos: "tonos veraniegos" (vago)
Restricción: Máximo 2 artistas repetidos
Disponibilidad: Catálogo limitado
Nota: Necesito esto urgente, tengo sesión en 10 min
```

### Instrucción al Subagente

```
Recibe la solicitud de DJ Carlos. Normalízala, marca ambigüedades, 
proporciona estructura para herramientas. 
Objetivo: Que el orquestador sepa qué preguntar a Carlos 
(si hay ambigüedad irresoluible) y qué hacer (best-effort o rechazar si tiempo).
```

### Output del Subagente

```json
{
  "parsed": {
    "duration_min": 59,
    "duration_max": 61,
    "phases": 1,
    "phase_1": {
      "bpm_min": 120,
      "bpm_max": 130,
      "tonalities": ["G_major", "D_major", "A_major", "E_major"],
      "bpm_progressive": false
    },
    "phase_2": null,
    "exclude_artists": [],
    "max_artist_repetitions": 2,
    "genre": "House / Tropical House (interpretación de 'veraniegos')",
    "mood": "sunny, uplifting"
  },
  "ambiguities": [
    {
      "field": "tonalidades",
      "issue": "'tonos veraniegos' es vago",
      "assumption": "Interpreté como tonalidades mayores (G/D/A/E): estrellas del verano en progresión armónica",
      "ask_dj": false
    },
    {
      "field": "bpm_progressive",
      "issue": "Dijo 'rango 120-130 no progresivo' (contradicción)",
      "assumption": "BPM fijo en rango, no progresión (típico de after-hours flat, no peak-time build)",
      "ask_dj": true
    },
    {
      "field": "urgencia",
      "issue": "'Sesión en 10 min' vs 'tiempo mínimo compilación ~2 min'",
      "assumption": "Viable pero ajustado: parse en 2s + search en 3s + compile en 4s = 9s restantes antes de timeout",
      "ask_dj": false
    }
  ],
  "urgency": {
    "stated_minutes": 10,
    "feasible": true
  },
  "confidence": 0.78,
  "next_step": "ask_dj: '¿BPM fijo 120-130 o progresivo hacia 130? ¿'tonos veraniegos' = majores (G/D/A/E) o algo más específico?'. Luego search_tracks con tonalidades mayores + max_repetitions=2."
}
```

**Lo que ve el orquestador:**
- ✅ Duración: 60 min (claro)
- ⚠️ BPM: ¿Fijo o progresivo? Pregunta a Carlos
- ⚠️ Tonos: ¿Mayores (interpretación parser) o otra cosa?
- ✅ Urgencia: Viable si responde en < 1 min
- ✅ Restricción: Max 2 artistas repetidos (claro)

---

## 5. Por qué es Subagente

| Aspecto | Justificación |
|---|---|
| **Contexto limpio** | Recibe solo texto + constraints catálogo. No ve conversación anterior. Si hay ambigüedad, orquestador (que sí ve contexto) pregunta al DJ. |
| **Rol distinto** | Parsing = lingüística + extracción. Las herramientas son búsqueda/validación de datos. |
| **Reutilizable** | Mismo parser para request_01 (clean), request_02 (messy), request_03 (complex). Messy es donde agrega más valor. |
| **Separación de concerns** | Orquestador = toma decisiones (preguntar DJ, guardar propuesta). Subagente = transforma entrada. |
| **Escalable** | Futura paralelización: N solicitudes → N parsers simultáneos. |

---

## 6. Costo

- **Tokens:** ~800 por solicitud (análisis de texto, sin herramientas)
- **Latencia:** < 3s
- **Sobrecosto vs. orquestador haciendo parse directo:** +~20%
- **Valor agregado:** Ambigüedad detectada + confianza (0-1) → orquestador decide si preguntar o proceder

**Rompe paridad si:** Solicitud clean (request_01) → parser + orquestador = redundancia. Pero es negligible (~800 tok = ~0.01 USD).

**Justificación total:** Request_02 (messy) > costo en request_01 (clean). Parser debe existir.

---

## 7. Integración en Flujo

```
Solicitud DJ (chat)
  ↓
[Orquestador] → Parser (subagente)
  ↓
Parser retorna parsed + ambiguities + confidence
  ↓
IF ambiguities con ask_dj=true:
  [Orquestador] → Pregunta al DJ
  [DJ responde]
  [Orquestador] → Refinement opcional (reenviar a Parser)
  ↓
[Orquestador] → validate_playlist_feasibility
  ↓
[Orquestador] → Compiler (futuro subagente, si fase=2)
  ↓
[Orquestador] → save_playlist_proposal
  ↓
[DJ aprueba en checkpoint]
  ↓
JSON final
```

---

## Notas

- **Asincronía:** Parser es determinista. No paralelizable internamente. Pero orquestador espera su resultado antes de decidir.
- **Reintentos:** No aplica (parsing no tiene "fallo" por catálogo). Si el parser dice "no entiendo", orquestador pregunta al DJ.
- **Mejoras futuras:** Parser podría llamar a `search_tracks_by_constraints` para validar disponibilidad tonalidades inline (contraejemplo: si DJ pide "F# menor" y no existe, avisar al orquestador). Pero eso es scope creep; por ahora, puramente texto.

# 🏗️ Arquitectura - DJ Playlist Generator v1.1

## Visión General

```
DJ Request (texto libre)
    ↓
┌─────────────────────────────────────────┐
│  MAIN AGENT (dj_agent.py)               │
│  ─ Orquesta el flujo                    │
│  ─ Decide cuándo invocar subagent       │
└─────────────────────────────────────────┘
    ↓
    ├─→ parse_dj_request() [local]
    │
    ├─→ [¿Constraints complejas?]
    │   ├─ SÍ → invoke SUBAGENT VALIDATOR
    │   │   ↓
    │   │   ┌────────────────────────────────────┐
    │   │   │ CONSTRAINT VALIDATOR SUBAGENT      │
    │   │   │ (constraint_validator_agent.py)    │
    │   │   │ ─ Identifica conflictos            │
    │   │   │ ─ Propone ajustes                  │
    │   │   │ ─ Retorna constraints refinadas    │
    │   │   └────────────────────────────────────┘
    │   └─ NO → continúa
    │
    ├─→ validate_feasibility() [MCP]
    │   ↓
    │   ┌────────────────────────────────────────┐
    │   │ MCP CATALOG SERVER                     │
    │   │ (catalog_mcp_server.py)                │
    │   │ ┌──────────────────────────────────┐   │
    │   │ │ search_tracks(bpm, tonality...)  │   │
    │   │ │ validate_feasibility(...)        │   │
    │   │ │ get_track_metadata(id)           │   │
    │   │ │ get_catalog_stats()              │   │
    │   │ └──────────────────────────────────┘   │
    │   │ BACKEND: CatalogService                │
    │   │ DATA: Mock ~100 tracks                 │
    │   └────────────────────────────────────────┘
    │
    ├─→ build_playlist() [greedy algo con MCP]
    │   └─→ search_tracks() (vía MCP)
    │
    ├─→ explain_playlist() [local]
    │
    ↓
OUTPUT (Playlist + Explicación + Ajustes aplicados)
```

---

## Flujo de Decisión (Cuándo invocar subagent)

```python
if constraints.phases is not None:              # Multi-fase
    → invoke_subagent()
elif constraints.no_artist_repeat:              # Sin repeticiones
    → invoke_subagent()
elif constraints.max_artist_repeats < 999:      # Restricción artista
    → invoke_subagent()
else:
    → procede normal
```

---

## Componentes

### 1. **Main Agent** (`dj_agent.py`)
- **Entrada:** Solicitud DJ (texto free)
- **Salida:** Playlist JSON + Explicación
- **Lógica:**
  - Parse local (regex)
  - Decide si subagent necesaria
  - Orquesta MCP calls
  - Construye playlist con greedy
  - Sintetiza respuesta

### 2. **MCP Catalog Server** (`catalog_mcp_server.py`)
- **Rol:** Centraliza acceso a catálogo
- **Tools expuestas:**
  1. `search_tracks(bpm_min, bpm_max, tonalities, exclude_artists, exclude_ids)`
  2. `get_track_metadata(track_id)`
  3. `validate_catalog_feasibility(bpm_start, bpm_end, tonalities, duration, no_repeat)`
  4. `get_catalog_stats()`
- **Backend:** `CatalogService` (static methods)
- **Data:** Mock MOCK_TRACKS (~100)

### 3. **Constraint Validator Subagent** (`constraint_validator_agent.py`)
- **Rol:** Especialista en validación y negociación
- **Cuándo:** Restricciones complejas/conflictivas
- **Entrada:** constraints dict + catalog_feedback
- **Salida:** ValidationResult (is_valid, refined_constraints, adjustments, explanation)
- **Métodos:**
  - `validate_and_negotiate()` → Valida y propone ajustes
  - `simulate_dj_negotiation()` → Simula diálogo DJ (futuro)

---

## Data Flow (Específico)

### Caso Normal (clean request)
```
REQUEST: "DJ María, 45 min, 115→128 BPM, Do Mayor, sin repetir"
  ↓
parse_dj_request()
  → ParsedConstraints(duration=45, bpm_start=115, bpm_end=128, no_repeat=True)
  ↓
should_validate_constraints() → TRUE (no_artist_repeat=True)
  ↓
MCP: validate_catalog_feasibility(115, 128, [C_major...], 45, True)
  → {"viable": true, "message": "✅ Viable: 20 tracks, 8 artistas"}
  ↓
build_playlist_greedy()
  → MCP: search_tracks(115, 128, [tonalities], [], [])
  → search_tracks(116, 128, [tonalities], [Adam Beyer], [1,2,3...])
  → ... (loop)
  ↓
explain_playlist()
  ↓
OUTPUT: "🎵 PLAYLIST PARA MARÍA\nBPM: 115→128\nDuración: 44.5 min\n1. [115] Adam Beyer - Teach Me..."
```

### Caso Complejo (conflict request)
```
REQUEST: "DJ Alex, 90 min, 110→115 BPM (rango estrecho), sin repetir, urgente"
  ↓
parse_dj_request()
  → ParsedConstraints(..., duration=90, bpm_start=110, bpm_end=115, no_repeat=True)
  ↓
should_validate_constraints() → TRUE (multi-restricción + no_repeat)
  ↓
MCP: validate_catalog_feasibility(110, 115, tonalities, 90, True)
  → {"viable": false, "message": "⚠️ Necesitas ~15 tracks sin repetir, pero rango BPM estrecho limita a 5"}
  ↓
INVOKE SUBAGENT VALIDATOR:
  Input: constraints + feedback
  ↓
  Subagent Claude: "Problema: 90 min con solo 5 tracks en rango 110-115"
  Propone: "Opción 1: Extender a 130 BPM (20 tracks)\n Opción 2: Permitir 2 repeticiones (10 tracks)"
  ↓
  Output: ValidationResult(
    is_valid=false,
    adjustments=["aumentar bpm_end a 130"],
    refined_constraints={bpm_start=110, bpm_end=130, ...},
    explanation="Expandimos rango BPM para viabilidad"
  )
  ↓
UPDATE constraints → bpm_end=130
  ↓
CONTINUE: build_playlist() con constraints refinadas
  ↓
OUTPUT: "Playlist ajustada con BPM 110→130 (solicitud original: 110→115)"
```

---

## MCP Protocol (Local Simulation)

En este MVP, MCP se simula localmente (sin stdio transport):
```python
# Agent calls:
tool_result = process_mcp_tool_call("search_tracks", {
    "bpm_min": 115,
    "bpm_max": 128,
    "tonalities": ["C_major"],
    "exclude_artists": ["Adam Beyer"]
})
# Returns JSON string
```

**Futuro:** Migrar a MCP server real con stdio transport si integran con otras herramientas.

---

## Puntos de Extensión

### 1. Integración con Spotify
```python
# En catalog_mcp_server.py CatalogService:
@staticmethod
def search_tracks_spotify(query, filters):
    token = get_spotify_token()
    return spotify_api.search(q=query, type="track", limit=50)
```

### 2. Beatmatching automático
```python
# Nueva tool MCP:
def get_compatible_beatmatch(track_id, next_track_id):
    # Capo position, key signature compatibility
    return {"capo": 0, "key": "C", "compatible": true}
```

### 3. Subagent de Feedback
```python
# Nuevo subagent:
class FeedbackAgentdj
```

---

## Testing

**4 casos de prueba en `run_all_tests.py`:**
1. **Clean:** Restricciones claras, sin conflicto
2. **Messy:** Ambiguedad, urgencia
3. **Complex:** Multi-fase, transiciones
4. **Conflict:** Restricciones conflictivas (activa subagent)

```bash
python3 run_all_tests.py
```

---

## Seguridad & Guardrails

1. **No fabricar tracks:** Solo MOCK_TRACKS
2. **Validación estricta:** MCP siempre valida antes de build
3. **Loop safety:** Máx 20 tracks por playlist
4. **Ajustes documentados:** Subagent explica qué se relajó
5. **No halucinar metadata:** get_track_metadata solo retorna si existe

---

## Performance

- **Latencia:** 10-30 seg/solicitud (Claude API)
- **Memoria:** ~2MB (mock catalog en RAM)
- **Costo:** ~0.01-0.02 USD/solicitud
- **Escalabilidad:** Mock→SQLite/Spotify sin cambiar código

---

**Creado:** 2026-11-11  
**Versión:** 1.1 (MCP + Subagent)  
**Status:** MVP, listo para demostración

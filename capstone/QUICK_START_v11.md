# 🚀 Quick Start v1.1 (MCP + Subagent)

## Qué es nuevo en 5 minutos

**Antes (v1.0):** 1 archivo (dj_agent.py) con todo inline  
**Ahora (v1.1):** 3 archivos Python con roles definidos + MCP

### Los 3 archivos nuevos/refactorizados

```
dj_agent.py (refactorizado)
├─ Agente principal que orquesta
├─ Decide cuándo llamar subagent
├─ Usa MCP para búsquedas
└─ Constructor de playlist

catalog_mcp_server.py (NUEVO)
├─ CatalogService = 4 métodos
├─ search_tracks()
├─ validate_feasibility()
├─ get_track_metadata()
├─ get_catalog_stats()
└─ Mock data ~100 tracks

constraint_validator_agent.py (NUEVO)
├─ Subagente especialista
├─ Identifica conflictos
├─ Propone ajustes
└─ Retorna constraints refinadas
```

---

## Flujo Rápido: Antes vs Ahora

### ANTES (v1.0)
```
INPUT → parse() → validate() → build() → explain() → OUTPUT
         (todo local, todo inline)
```

### AHORA (v1.1)
```
INPUT → parse()
        → ¿Restricciones complejas?
           ├─ SÍ: INVOKE SUBAGENT
           │      ├─ query MCP (validate_feasibility)
           │      ├─ propose adjustments
           │      └─ return refined constraints
           └─ NO: continuar
        → build() [usa MCP search_tracks]
        → explain()
        → OUTPUT
```

---

## Dónde Ver Qué

| Si quiero entender | Leo |
|-------------------|-----|
| Cómo funciona el MCP | ARCHITECTURE.md (sección "MCP Protocol") |
| Cuándo se invoca subagent | CLAUDE.md sección 6 + dj_agent.py: `should_validate_constraints()` |
| El flujo visual | ARCHITECTURE.md (top) |
| Qué cambió exactamente | REFACTOR_SUMMARY.md |
| Todas las decisiones | CLAUDE.md (11 secciones completas) |

---

## 3 Test Cases Clave

### Test 1: Clean → No subagent
```
REQUEST: DJ María, 45 min, 115→128 BPM, Do Mayor, sin repetir
FLOW: parse → MCP validate → build → explain
SUBAGENT: NO (restricción simple)
```

### Test 3: Complex → SÍ subagent
```
REQUEST: DJ Alex, 90 min, 2 fases (110→120, 120→130), transiciones suaves
FLOW: parse → ¿COMPLEX? YES → invoke SUBAGENT → build → explain
SUBAGENT: SÍ (multi-fase activa validador)
```

### Test 4: Conflict → SÍ subagent (prueba el nuevo!)
```
REQUEST: DJ Alex, 90 min, 110→115 BPM SOLAMENTE, sin repetir
PROBLEM: Rango muy estrecho, no hay 15 tracks disponibles
SUBAGENT: ✅ Propone "expandir a 130" o "permitir 2 repeticiones"
RESULT: Playlist con constraints ajustadas + explicación
```

---

## Ejecutar

```bash
# Setup (una vez)
cd /workshop/capstone
source venv/bin/activate
pip install anthropic

# Test uno
python3 dj_agent.py

# Todos (incluyendo subagent test)
python3 run_all_tests.py
```

---

## Architecture Visual

```
MAIN AGENT (dj_agent.py)
    ↓
    ├─→ parse_dj_request() [LOCAL]
    │
    ├─→ should_validate_constraints()
    │   ├─ Phases? → YES
    │   ├─ No repeat? → YES
    │   └─ Restrict artist? → YES
    │       DECISION: INVOKE SUBAGENT
    │   ↓
    │   SUBAGENT (constraint_validator_agent.py)
    │   ├─ Query MCP: validate_feasibility()
    │   ├─ Analyze conflicts
    │   ├─ Propose adjustments
    │   └─ Return refined constraints
    │
    ├─→ validate_feasibility() [MCP]
    │   ↓
    │   MCP CATALOG SERVER (catalog_mcp_server.py)
    │   ├─ search_tracks()
    │   ├─ get_track_metadata()
    │   ├─ validate_feasibility()
    │   └─ get_catalog_stats()
    │
    ├─→ build_playlist() [calls MCP search_tracks in loop]
    │
    ├─→ explain_playlist() [LOCAL]
    │
    ↓
    OUTPUT
```

---

## Requisitos del Curso Cumplidos

✅ **MCP Server:** `catalog_mcp_server.py` con 4 tools  
✅ **Subagent:** `constraint_validator_agent.py` con rol propio  
✅ **Separación clara:** MCP = búsquedas, Subagent = validación, Main = orquestación  
✅ **Justificado:** Ambos se usan de verdad en cases reales

---

## Próximos Pasos (Opcional)

1. **Entender MCP real:** Actualmente local, podría ser stdio transport
2. **Mejorar subagent:** Agregar negociación interactiva con DJ
3. **Integrar Spotify:** Reemplazar mock con API real
4. **Agregar feedback:** DJ valida, subagent refina más

---

## Cheat Sheet

```python
# Si quiero entender MCP:
from catalog_mcp_server import get_mcp_tools, process_mcp_tool_call
tools = get_mcp_tools()  # Lista de 4 tools
result = process_mcp_tool_call("search_tracks", {...})

# Si quiero entender subagent:
from constraint_validator_agent import ConstraintValidatorAgent
validator = ConstraintValidatorAgent()
result = validator.validate_and_negotiate(constraints, feedback)
# Returns: ValidationResult(is_valid, refined_constraints, adjustments, explanation)

# Si quiero ejecutar agente:
from dj_agent import DJPlaylistAgent
agent = DJPlaylistAgent()
agent.run("DJ Maria, 45 min, 115-128 BPM...")
```

---

**Versión:** 1.1  
**Fecha:** 2026-11-11  
**Status:** ✅ Completo, testeable, demostrable

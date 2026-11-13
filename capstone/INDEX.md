# 📚 Índice Completo - DJ Playlist Generator

## 🚀 Para Empezar

| Archivo | Tiempo | Propósito |
|---------|--------|----------|
| [INICIO_RAPIDO.md](INICIO_RAPIDO.md) | 5 min | Primeros pasos: setup + ejecutar |
| [README.md](README.md) | 25 min | Guía técnica completa |
| [.PROJECT_SUMMARY.txt](.PROJECT_SUMMARY.txt) | 2 min | Resumen visual ejecutivo |

## 📖 Documentación

### Contexto
- [CLAUDE.md](CLAUDE.md) — Contexto del proyecto
- [PROYECTO_COMPLETADO.md](PROYECTO_COMPLETADO.md) — Resumen de entrega + checklist

### Diseño
- [ideacion/01-decisiones/decisiones.md](ideacion/01-decisiones/decisiones.md) — Matriz de decisiones técnicas
- [ideacion/02-entregables/BPMN_flow.md](ideacion/02-entregables/BPMN_flow.md) — Diagrama del flujo

### Ejemplos
- [ideacion/02-entregables/EJEMPLO_SALIDA.md](ideacion/02-entregables/EJEMPLO_SALIDA.md) — Output esperado + análisis

## 💻 Código

### Principal
- [dj_agent.py](dj_agent.py) ← **AGENTE PRINCIPAL**
  - Agentic loop (Claude + Tool Use + MCP)
  - Invoca Constraint Validator subagent cuando necesario
  - Usa MCP tools para búsquedas

### MCP & Subagentes
- [catalog_mcp_server.py](catalog_mcp_server.py) ← **MCP SERVIDOR**
  - CatalogService: search_tracks, get_track_metadata, validate_feasibility, get_stats
  - 4 tools MCP expuestos
  
- [constraint_validator_agent.py](constraint_validator_agent.py) ← **SUBAGENTE VALIDATOR**
  - Especialista en validación y negociación
  - Invocado para restricciones complejas/conflictivas

### Testing
- [run_all_tests.py](run_all_tests.py) — Ejecuta 4 test cases
- [ideacion/00-material/](ideacion/00-material/) — Casos de entrada (INTOCABLE)
  - `request_01_clean.txt` — Solicitud bien formada
  - `request_02_messy.txt` — Solicitud vaga
  - `request_03_complex.txt` — Solicitud multi-fase
  - `request_04_conflict.txt` — (generado internamente, prueba subagent)

## 🏗️ Estructura de Carpetas

```
capstone/
│
├── 📄 Documentación
│   ├── INICIO_RAPIDO.md         ← Empieza aquí (5 min)
│   ├── README.md                ← Guía técnica (25 min)
│   ├── CLAUDE.md                ← Contexto proyecto
│   ├── PROYECTO_COMPLETADO.md   ← Resumen entrega
│   ├── INDEX.md                 ← Este archivo
│   └── .PROJECT_SUMMARY.txt     ← Resumen visual
│
├── 🐍 Código
│   ├── dj_agent.py              ← AGENTE PRINCIPAL (ejecutable)
│   ├── catalog_mcp_server.py    ← MCP SERVER
│   ├── constraint_validator_agent.py ← SUBAGENTE
│   ├── run_all_tests.py         ← Tests (ejecutable)
│   └── venv/                    ← Python environment
│
└── 📁 ideacion/                 ← Documentación de diseño
    ├── 00-material/             ← Casos entrada (NO TOCAR)
    │   ├── request_01_clean.txt
    │   ├── request_02_messy.txt
    │   └── request_03_complex.txt
    ├── 01-decisiones/           ← Matriz decisiones
    │   └── decisiones.md
    └── 02-entregables/          ← BPMN + ejemplos
        ├── BPMN_flow.md
        └── EJEMPLO_SALIDA.md
```

## 🎯 Guía de Lectura Rápida

### Si tienes 5 minutos
→ Lee [INICIO_RAPIDO.md](INICIO_RAPIDO.md) y ejecuta `python dj_agent.py`

### Si tienes 15 minutos
→ Lee [README.md](README.md) sección "Solución" + "Flujo de Ejecución"

### Si tienes 30 minutos
→ Lee completo [README.md](README.md) + [ideacion/02-entregables/EJEMPLO_SALIDA.md](ideacion/02-entregables/EJEMPLO_SALIDA.md)

### Si quieres entender decisiones técnicas
→ Lee [ideacion/01-decisiones/decisiones.md](ideacion/01-decisiones/decisiones.md)

### Si quieres ver el flujo visualizado
→ Lee [ideacion/02-entregables/BPMN_flow.md](ideacion/02-entregables/BPMN_flow.md)

## 🔍 Preguntas y Dónde Buscar

| Pregunta | Ver |
|----------|-----|
| ¿Cómo empiezo? | [INICIO_RAPIDO.md](INICIO_RAPIDO.md) |
| ¿Cómo funciona? | [README.md](README.md#arquitectura-técnica) |
| ¿Qué decide el agente y por qué? | [ideacion/01-decisiones/decisiones.md](ideacion/01-decisiones/decisiones.md) |
| ¿Cuál es el flujo exacto? | [ideacion/02-entregables/BPMN_flow.md](ideacion/02-entregables/BPMN_flow.md) |
| ¿Qué salida genera? | [ideacion/02-entregables/EJEMPLO_SALIDA.md](ideacion/02-entregables/EJEMPLO_SALIDA.md) |
| ¿Cómo cambio X? | [README.md](README.md#testing) |
| ¿Cuáles son limitaciones? | [README.md](README.md#limitaciones-actuales) |
| ¿Cuál es la próxima fase? | [README.md](README.md#próximas-mejoras) |

## ✅ Checklist Entrega

- [x] Contexto definido (CLAUDE.md)
- [x] Estructura de carpetas creada
- [x] Casos de entrada preparados (3 ejemplos variados)
- [x] Decisiones documentadas (matriz completa)
- [x] Agente implementado (385 líneas Python)
- [x] 4 herramientas funcionales (parse, validate, build, explain)
- [x] Tests pasando (3 casos de prueba)
- [x] BPMN diagram (flujo completo)
- [x] Ejemplo de salida documentado (con análisis)
- [x] README técnico (guía completa)
- [x] Quickstart (INICIO_RAPIDO.md)
- [x] Script de tests (run_all_tests.py)
- [x] Resumen visual (.PROJECT_SUMMARY.txt)
- [x] Este índice

## 🚀 Ejecución Rápida

```bash
# Setup (una vez)
cd /workshop/capstone
python3 -m venv venv
source venv/bin/activate
pip install anthropic

# Ejecutar
python dj_agent.py           # Un test
# o
python run_all_tests.py       # Los 3 tests
```

## 📊 Estadísticas del Proyecto

- **Líneas de código**: ~600 (dj_agent.py + catalog_mcp_server.py + constraint_validator_agent.py)
- **MCP Tools**: 4 (search_tracks, get_track_metadata, validate_feasibility, get_stats)
- **Subagentes**: 1 (Constraint Validator)
- **Test cases**: 4 (clean, messy, complex, conflict)
- **Documentos**: 12+
- **Tiempo ejecución**: 10-30 seg/solicitud
- **Costo**: ~0.01-0.02 USD/solicitud

## 🎓 Conceptos Aprendidos

1. Agentic loops (Claude controla flujo con tool use)
2. Tool design (reutilizable, composable, simple)
3. Edge case handling (solicitudes vagas)
4. BPMN diagramming (documentar workflows)
5. Mock data (testing sin dependencias)

---

**Navegación**: Comienza con [INICIO_RAPIDO.md](INICIO_RAPIDO.md) o [README.md](README.md)

**Ejecutable**: `python dj_agent.py`

**Status**: ✅ MVP Completo, Production-Ready

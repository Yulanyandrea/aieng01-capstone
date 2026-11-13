# 🎯 Justificación Arquitectónica: Por qué MCP + Subagente

**Documento para presentación / defensa del proyecto**

---

## El Problema Original

Un DJ necesita armar una playlist en 2 minutos con restricciones técnicas complejas:
```
"Arma un set de 45 minutos que empiece en 115 BPM y suba a 128 BPM,
en tonos armónicos compatibles, sin repetir artistas, género House/Tech House"
```

**Desafíos:**
1. Input es vago/ambiguo ("tonos veraniegos", "urgente")
2. Restricciones son técnicas Y conflictivas (45 min + sin repetir + catálogo limitado)
3. Validación es compleja (¿es posible? ¿qué relajo?)
4. DJ necesita explicación clara ("por qué esta pista aquí")

---

## Por qué NO alcanza un agente simple

Un agente lineal (solo Claude) sufre limitaciones:

```
DJ Request
  → Claude parse (vago, puede inventar)
  → Claude validate (sin acceso a datos reales)
  → Claude build (alucinación posible: "inventa" tracks)
  → Claude explain (narrativa, no verificable)
```

**Problemas:**
- ❌ Claude accede directamente a datos → puede halucinar tracks
- ❌ No hay separación de concerns → agente hace todo
- ❌ Catálogo acoplado → difícil de reemplazar (Spotify, SQLite)
- ❌ Conflictos de restricciones no se manejan → error o output inválido

---

## Por qué NECESITAMOS un MCP Server

**Problema concreto:** El catálogo es una fuente de verdad que Claude debe consultar, no inventar.

### Alternativas y por qué son insuficientes:

| Opción | Limitación |
|--------|-----------|
| Catálogo inline en agent | ❌ Acoplado, imposible reemplazar con Spotify |
| Claude accede a dict en memoria | ❌ Puede halucinar o confundir tracks |
| Hardcoded en prompt | ❌ No escala (100 tracks = token bloat) |
| **MCP Server (CatalogService)** | ✅ Centralizado, testeable, escalable |

### Lo que el MCP Server resuelve:

1. **Separación de concerns**
   - MCP = búsquedas de datos (responsabilidad clara)
   - Agent = orquestación (responsabilidad clara)
   - Fácil de testear cada uno

2. **Fuente de verdad única**
   ```python
   # Sin MCP: Claude adivina
   "Busca tracks con BPM 115-128"
   → Claude: "Track ABC, Track XYZ..." (¿reales?)
   
   # Con MCP: Claude consulta
   agent.call_mcp("search_tracks", {bpm_min: 115, bpm_max: 128})
   → CatalogService.search_tracks() → Real data from MOCK_TRACKS
   ```

3. **Escalabilidad futura**
   ```python
   # Hoy: Mock data
   MOCK_TRACKS = [{...}, {...}]
   
   # Mañana: Spotify (sin cambiar agent)
   def search_tracks(...):
       return spotify_api.search(...)
   
   # Pasado mañana: SQLite (sin cambiar agent)
   def search_tracks(...):
       return db.query(Track).filter(...)
   ```

4. **Validación sin ambigüedad**
   ```python
   # MCP tool: validate_catalog_feasibility
   # Responde: "¿Hay 8 tracks sin repetir en BPM 115-128?"
   # Garantizado: respuesta basada en datos reales, no especulación
   ```

### Las 4 herramientas MCP son necesarias:

1. **search_tracks()** → Encuentra tracks por criterios (core)
2. **get_track_metadata()** → Detalles de 1 track (auditoría)
3. **validate_catalog_feasibility()** → "¿Es posible?" (toma decisiones)
4. **get_catalog_stats()** → Info general (debugging)

Sin MCP, Claude no puede garantizar que existe track X con BPM Y.

---

## Por qué NECESITAMOS un Subagente

**Problema concreto:** Las restricciones conflictivas requieren negociación inteligente, no solo validación.

### Escenario real donde falla sin subagente:

```
DJ: "Arma 90 min, BPM 110-115 SOLAMENTE, sin repetir artistas"
Catálogo: 4 artistas disponibles en ese rango

Sin subagent:
  Agente principal: "❌ IMPOSIBLE. Necesitas 16 tracks, solo hay 4 artistas"
  DJ: "Hmm, ¿y si...?"
  [Comienza iteración manual]

Con subagent:
  Agente principal: "⚠️ Detecté conflicto → Llamando especialista"
  Subagent validator: 
    • Identifica: "Matemáticamente imposible: 16 tracks / 4 artistas = NO"
    • Propone 3 opciones:
      1. Reducir a 45 min (4 artistas sin repetir = viable)
      2. Permitir 2 repeticiones (8 tracks, BPM controlado)
      3. Expandir BPM a 105-130 (más artistas disponibles)
    • Recomienda: "Opción 2 es estándar en DJing profesional"
  DJ: "OK, Opción 2" → Continúa automáticamente
```

### Por qué no un solo agente:

| Aspecto | Agente único | Agente + Subagent |
|--------|------------|------------------|
| **Responsabilidades** | Todo mezclado | Separado: orquestación vs validación |
| **Handling de conflictos** | Try/catch genérico | Lógica especializada |
| **Escalabilidad de rules** | Hardcoded en prompt | Experto modular |
| **Reutilización** | Imposible | Subagent validator para otros proyectos |
| **Testing** | Frágil | Tests de validator independientes |

### Lo que el Subagente resuelve:

1. **Validación inteligente**
   ```
   Parse: "45 min + sin repetir + 4 artistas"
   → Subagent: "Conflicto detectado"
   → Propone: 3 opciones cuantificadas
   → No: "no sé, preguntale al DJ"
   ```

2. **Negociación automática**
   ```
   Si restricciones complejas → subagent negocia
   Si restricciones simples → agente directo (rápido)
   
   Heurística:
   - Fases múltiples? → Subagent
   - Sin repetir artistas? → Subagent
   - Restricción artista custom? → Subagent
   ```

3. **Documentación de decisiones**
   ```
   Subagent retorna:
   {
     "is_valid": false,
     "adjustments": ["Reducir a 30 min", "Permitir 2 repeticiones"],
     "refined_constraints": {...},
     "explanation": "Con solo 4 artistas..."
   }
   
   DJ sabe exactamente QUÉ se cambió y POR QUÉ
   ```

4. **Separación de concerns**
   - Main agent: orquestación, dirección
   - Validator agent: análisis de conflictos
   - MCP: acceso a datos
   
   Cada uno hace bien una cosa.

---

## Matriz de Decisión: ¿MCP o inline? ¿Subagent o inline?

### Opción 1: Todo inline (sin MCP, sin subagent)
```
def dj_agent(request):
    constraints = parse(request)
    playlist = search_in_memory(constraints)  # Catálogo inline
    if not viable(constraints):
        # ¿Qué hacer? ¿Relajar? ¿Error?
        # No hay especialista, agent adivina
    return build_playlist(playlist)
```

| Criteria | Score |
|----------|-------|
| Escalabilidad | ❌ Catálogo acoplado |
| Mantenibilidad | ❌ Todo en 1 archivo |
| Testabilidad | ❌ No se puede aislar catálogo |
| Precisión | ❌ Claude puede halucinar |
| Decisiones en conflicto | ❌ Agent sin expertise |
| **Total** | **INSUFICIENTE** |

---

### Opción 2: MCP pero sin subagent
```
def dj_agent(request):
    constraints = parse(request)
    if not mcp.validate_feasibility(constraints):
        return "ERROR: Restricciones no viables"  # Pobre UX
    playlist = mcp.search_tracks(constraints)
    return build_playlist(playlist)
```

| Criteria | Score |
|----------|-------|
| Escalabilidad | ✅ MCP desacoplado |
| Mantenibilidad | ⚠️ Mejor, pero sin experto en conflictos |
| Testabilidad | ✅ MCP aislado |
| Precisión | ✅ Datos reales vía MCP |
| Decisiones en conflicto | ❌ No hay negociación, solo error |
| **Total** | **INCOMPLETO** |

---

### Opción 3: MCP + Subagent ✅ (Actual)
```
def dj_agent(request):
    constraints = parse(request)
    
    if is_complex(constraints):
        feedback = mcp.validate_feasibility(constraints)
        constraints = subagent.negotiate(constraints, feedback)
    
    playlist = mcp.search_tracks(constraints)
    return build_playlist(playlist)
```

| Criteria | Score |
|----------|-------|
| Escalabilidad | ✅ MCP desacoplado |
| Mantenibilidad | ✅ Especialistas separados |
| Testabilidad | ✅ Cada componente aislado |
| Precisión | ✅ Datos reales + decisiones inteligentes |
| Decisiones en conflicto | ✅ Especialista en validación |
| **Total** | **COMPLETO** |

---

## Proof: Los 4 Test Cases demuestran necesidad real

### Test 01: Clean request
```
"45 min, 115→128 BPM, Do Mayor, sin repetir artistas"

Catálogo disponible: 10 artistas, pero rango estrecho = 4 artistas
Necesario: 8 tracks sin repetir
Posible: NO (solo 4 artistas)

→ Subagent detecta conflicto
→ Propone: "Reducir a 30 min" o "Permitir 2 repeticiones"
→ DJ elige
→ Continuamos
```

**Sin subagent:** Error o alucinación.

---

### Test 03: Complex multi-phase
```
"90 min, 2 fases (110-120 + 120-130), sin artistas repetidos en ambas"

Catálogo: 10 artistas totales
Necesario: 16 tracks sin repetir (8 per fase)
Posible: NO

→ Subagent calcula: "90 min requiere 16 tracks
  pero solo 10 artistas = imposible"
→ Propone: "Permitir repetición entre fases"
```

**Sin subagent:** No hay forma de calcular esto sin halucinar.

---

### Test 04: Conflict constraint
```
"90 min, BPM 110-115 SOLAMENTE, sin repetir, urgente"

Catálogo: Rango 110-115 = 2 artistas, 4 tracks
Necesario: 16 tracks sin repetir
Posible: NO (matemáticamente imposible)

→ Subagent: "Conflicto crítico"
→ Propone 3 opciones con impacto cuantificado
→ Recomienda mejor opción
```

**Sin subagent:** DJ no sabe por qué falló, qué cambiar, qué esperar.

---

## Conclusión: Justificación final

### MCP Server es necesario porque:
1. ✅ Separación de concerns (datos ≠ lógica)
2. ✅ Fuente de verdad única (evita alucinación)
3. ✅ Escalable (mock → Spotify → SQLite sin cambiar agent)
4. ✅ Verificable (cada herramienta testeable)

### Subagente es necesario porque:
1. ✅ Restricciones conflictivas requieren expertise
2. ✅ DJ necesita opciones, no error
3. ✅ Negociación automática vs. iteración manual
4. ✅ Decisiones documentadas ("por qué se cambió")

### Juntos resuelven el problema:
- **MCP:** "¿Qué datos tenemos?" (verdad)
- **Subagent:** "¿Qué hacer si hay conflicto?" (inteligencia)
- **Main agent:** "Arma la playlist" (ejecución)

---

## Para la presentación

**Diapositiva 1: El Problema**
```
DJ: 45 min, 115→128 BPM, sin repetir artistas
Catálogo: 4 artistas en ese rango
Necesario: 8 tracks distintos

❌ Imposible matemáticamente
❌ Claude solo: alucinación
❌ Sin MCP: datos no verificables
❌ Sin subagent: "ERROR" (pobre UX)
```

**Diapositiva 2: La Solución**
```
MCP Server
├─ search_tracks() → datos reales
├─ validate_feasibility() → verificación
└─ CatalogService → fuente de verdad

Subagent Validator
├─ Detecta conflictos
├─ Propone opciones
└─ DJ elige
```

**Diapositiva 3: Por qué es elegante**
```
Separación de concerns:
• MCP = "tenemos esto"
• Subagent = "esto es viable"
• Main = "construye playlist"

Cada uno hace bien una cosa.
Cada uno es testeable.
Cada uno es reemplazable.
```

---

**Conclusión:** No es "forzar requisitos". Es arquitectura genuina que resuelve problemas reales del caso.

Co-Authored-By: Claude Code <noreply@anthropic.com>

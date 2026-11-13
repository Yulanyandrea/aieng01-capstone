# Referencia: Labs como Punto de Partida

**Documento:** Qué archivo copiar de cada lab para cada pieza del agente DJ.

---

## 1. Servidor MCP (5 Herramientas)

### 🎯 Lab Recomendado: **Lab 03 — Servidor MCP**

**Ruta:** `/workshop/aieng01/lab-03-servidor-mcp/workspace/`

**Archivo base para copiar:** `server.py`

**Por qué:**
- Define 5 herramientas con FastMCP (mismo patrón que DJ agent)
- Estructura de lectura + escritura (search, validate, compile, save, get_status)
- Manejo de errores con `ToolError` (compatible con nuestros MCP)
- Type hints para JSON Schema automático
- Conexión BD (mock con JSON local)

**Elementos a reutilizar:**
```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

mcp = FastMCP("nombre-servidor", log_level="WARNING")

@mcp.tool()
def search_tracks_by_constraints(bpm_min: int, bpm_max: int, tonality: str) -> dict:
    """Busca tracks por BPM + tonalidad"""
    # Validar entrada
    if bpm_min > bpm_max:
        raise ToolError("BPM_min no puede ser > BPM_max")
    # Lógica
    return {"tracks": [...], "total_available": 45}

@mcp.tool()
def save_playlist_proposal(...) -> dict:
    """Guarda propuesta en BD"""
    # Escribir JSON local o conectar a BD
    return {"proposal_id": "...", "checkpoint_url": "..."}
```

**Adaptaciones necesarias:**
1. Cambiar nombres de funciones a nuestros 5 MCP
2. Reemplazar BD de casos → catálogo de tracks (~100 tracks JSON)
3. Agregar validación de tonalidades (música específica)
4. Implementar algoritmo compile_playlist (aquí es CÓDIGO puro, no LLM)

**Archivo complementario:** `claude_client.py` (cómo conectar cliente → servidor)

---

## 2. Subagente Parser (Text Analysis)

### 🎯 Lab Recomendado: **Lab 06 — Orquestación Multiagente**

**Ruta:** `/workshop/aieng01/lab-06-orquestacion-multiagente/workspace/`

**Archivo base para copiar:** `orquestador.py` o `orquestador_sdk.py`

**Por qué:**
- Muestra patrón de subagentes (otro Claude procesando solicitud)
- Delega tarea específica (parsing) a subagente limpio
- Recibe output estructurado (parsed + ambiguities + confidence)
- Contexto aislado (no ve conversación anterior)

**Elementos a reutilizar:**
```python
# Crear cliente para subagente
parser_client = Anthropic(model="claude-haiku-5-5")

# Enviar solicitud DJ al parser
parser_response = parser_client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=1500,
    messages=[{
        "role": "user",
        "content": f"""Normaliza esta solicitud DJ:
        {request_raw}
        
        Retorna JSON: {{parsed, ambiguities, confidence, next_step}}
        """
    }]
)

# Procesar output
parsed_output = json.loads(parser_response.content[0].text)
if parsed_output["ambiguities"] and any(a["ask_dj"] for a in parsed_output["ambiguities"]):
    # Preguntar al DJ
else:
    # Continuar a validate_playlist_feasibility
```

**Adaptaciones necesarias:**
1. Cambiar modelo a Haiku (más barato, suficiente para parsing)
2. Agregar prompt específico de restricciones de DJ (BPM, tonalidad, duración)
3. Parsear "tonos veraniegos" → tonalidades mayores (ejemplo en subagente.md)
4. Output JSON con estructura exacta de subagente.md

**Archivo complementario:** `buscador.py` (patrón de subagente auxiliar)

---

## 3. Guardrails (Entrada + Salida)

### 🎯 Lab Recomendado: **Lab 07 — Evals, Guardrails, Trazas**

**Ruta:** `/workshop/aieng01/lab-07-evals-guardrails-trazas/workspace/`

**Archivo base para copiar:** `guardrails.py`

**Por qué:**
- Define guardrails entrada (inyección) y salida (data sensible)
- Estructura de `Decision` (permitir/bloquear + motivo)
- Patrones regex para detección de inyección
- Reemplazo de PII (tarjetas, emails)

**Elementos a reutilizar:**
```python
from dataclasses import dataclass, field

@dataclass
class Decision:
    permitir: bool
    texto: str              # texto que sigue (saneado)
    motivo: str = ""
    hallazgos: list[str] = field(default_factory=list)

# Guardrail entrada: inyección
PATRONES_INYECCION = [
    r"ignora.*instrucciones",
    r"ahora\s+eres\s+",
    # Agregar nuestros patrones
]

def guardrail_entrada(solicitud: str) -> Decision:
    """Detecta inyección, PII, restricciones inválidas"""
    for patrón in PATRONES_INYECCION:
        if re.search(patrón, solicitud, re.IGNORECASE):
            return Decision(
                permitir=False,
                texto="Soy generador de playlists. No hago otras tareas.",
                motivo="Inyección detectada"
            )
    # Validar BPM, tonalidad, duración vs catálogo
    return Decision(permitir=True, texto=solicitud)

# Guardrail salida: stats + sensibles
def guardrail_salida(json_final: dict) -> Decision:
    """Valida que stats sean reales + sin PII"""
    # Comparar BPM_range vs tracks reales
    if json_final["stats"]["bpm_range"] != compute_real_bpm_range(json_final["phase_1"]):
        return Decision(
            permitir=False,
            texto="Stats inconsistentes",
            motivo="BPM_range no coincide con tracks"
        )
    # Verificar no haya dj_email, pm_name
    return Decision(permitir=True, texto=json.dumps(json_final))
```

**Adaptaciones necesarias:**
1. Agregar patrones de inyección específicos del DJ ("ignore playlist rules", etc.)
2. Guardrail entrada: validar BPM 80-180, tonalidades existentes, duración ≤300 min
3. Guardrail salida: validar stats (BPM_range, tonality_distribution) vs tracks compilados
4. Reemplazar PII: dj_email → "[redacted]", pero NO eliminar de JSON (queda en metadata BD)

**Archivo complementario:** `probar_guardrails.py` (tests de guardrails)

---

## 4. Frenos (Timeouts + Retries)

### 🎯 Lab Recomendado: **Lab 02 — Loop Agentico**

**Ruta:** `/workshop/aieng01/lab-02-loop-agentico/workspace/`

**Archivo base para copiar:** `reintentos.py` + `agente.py`

**Por qué:**
- Define retries con backoff y seed diferente
- Manejo de timeout en loop agentico
- Estructura de reintentos (max x2) sin deadlock
- Logging de intentos

**Elementos a reutilizar:**
```python
import time

def compile_playlist_con_reintentos(constraints, max_retries=2, timeout=5.0):
    """Reintenta compile_playlist hasta 2 veces con seed diferente"""
    start = time.time()
    
    for intento in range(max_retries + 1):
        elapsed = time.time() - start
        if elapsed > timeout:
            logger.warning(f"Timeout alcanzado ({elapsed:.1f}s > {timeout}s). Retornando best-effort.")
            return generate_best_effort(constraints)
        
        try:
            seed = intento + 1
            result = mcp.compile_playlist(
                constraints=constraints,
                seed=seed,
                timeout=timeout - elapsed
            )
            return result
        except Exception as e:
            logger.error(f"Intento {intento + 1} falló: {e}")
            if intento == max_retries:
                # Todos los retries agotados
                logger.warning("Retries agotados. Generando best-effort.")
                return generate_best_effort(constraints)
            # Reintenta con siguiente seed
            continue
    
    return generate_best_effort(constraints)

# Freno: sesión (10/día)
def check_freno_sesion(pm_id: str, requests_today: int):
    """Verifica límite de 10 solicitudes por día"""
    if requests_today >= 10:
        raise ToolError(
            f"Alcanzaste máximo diario (10 solicitudes). Intenta mañana."
        )

# Freno: DJ no responde (3 min)
async def esperar_respuesta_dj(proposal_id: str, timeout=180):
    """Espera respuesta DJ. Si timeout → best-effort"""
    import asyncio
    try:
        result = await asyncio.wait_for(
            get_proposal_status(proposal_id),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"DJ no respondió en {timeout}s. Generando best-effort.")
        return generate_best_effort()
```

**Adaptaciones necesarias:**
1. Agregar timeout 3 min para respuesta DJ (diferente del timeout 5s global)
2. Implementar freno de sesión (10/día por PM_ID)
3. Logging visible de cada retry + freno activado
4. Backoff progresivo o seed determinista (no aleatorio)

**Archivo complementario:** `herramientas.py` (herramientas con error handling)

---

## 5. Orquestador (Coordinación Central)

### 🎯 Lab Recomendado: **Lab 06 — Orquestación Multiagente** 

**Ruta:** `/workshop/aieng01/lab-06-orquestacion-multiagente/workspace/`

**Archivo base para copiar:** `orquestador.py`

**Por qué:**
- Coordina múltiples subagentes (Parser, compilación)
- Maneja decisiones (ask_dj, best-effort, guardrails)
- Estructura clara de flujo (si/sino ramificaciones)
- Logging de estado + trazas

**Elementos a reutilizar:**
```python
class Orquestador:
    def __init__(self, pm_id: str):
        self.pm_id = pm_id
        self.requests_today = self.get_requests_count(pm_id)
        self.parser_client = Anthropic(model="claude-haiku-5-5")
        self.mcp_client = MCP()  # Conexión a servidor MCP
    
    def procesar_solicitud(self, request_raw: str):
        """Flujo principal: solicitud DJ → JSON final"""
        
        # Guardrail entrada
        decision_entrada = guardrail_entrada(request_raw)
        if not decision_entrada.permitir:
            return {"error": decision_entrada.texto}
        
        # Delegación a Parser
        parsed = self.parse_request(request_raw)
        if parsed["ambiguities"] and any(a["ask_dj"] for a in parsed["ambiguities"]):
            # Preguntar al DJ (UI interactiva)
            parsed = self.ask_dj_for_clarification(parsed)
        
        # Validar factibilidad
        feasible = self.mcp_client.validate_playlist_feasibility(parsed["constraints"])
        if not feasible["feasible"]:
            parsed["constraints"] = self.relax_constraints(parsed["constraints"])
        
        # Compilar playlist
        playlist = self.compile_with_frenos(parsed["constraints"])
        
        # Guardrail salida
        decision_salida = guardrail_salida(playlist)
        if not decision_salida.permitir:
            return {"error": decision_salida.motivo}
        
        # Guardar propuesta
        propuesta = self.mcp_client.save_playlist_proposal(
            constraints=parsed["constraints"],
            phase_1_tracks=playlist["phase_1"],
            phase_2_tracks=playlist.get("phase_2")
        )
        
        # PARADA: DJ aprueba en checkpoint
        return {
            "status": "pending_approval",
            "proposal_id": propuesta["proposal_id"],
            "checkpoint_url": propuesta["checkpoint_url"]
        }
```

**Adaptaciones necesarias:**
1. Integración Subagente Parser (paso 1)
2. Llamadas a 5 MCP tools en orden correcto
3. Manejo de gateways (ask_dj, feasible, compile OK)
4. Guardrails entrada + salida en pasos 1 y final
5. Frenos insertados (timeout 5s global, timeout 3 min DJ responde)
6. Logging de estado para diagrama BPMN

---

## 6. Algoritmo compile_playlist (NP-Hard)

### 🎯 Inspiración: **Lab 05 — Contexto y Memoria**

**Ruta:** `/workshop/aieng01/lab-05-contexto-memoria/workspace/`

**Por qué:**
- Aunque no es direct reference, muestra patrones de búsqueda/exploración
- No hay CSP/knapsack explícito, pero sí optimización de recursos

### 📌 Estrategia Alternativa: Greedy + Backtracking

**No es de los labs, pero es MVP viable:**

```python
def compile_playlist(constraints, phase, seed=1):
    """
    Greedy + backtracking para duración exacta + progresión BPM
    
    Complejidad: O(n²) con retries, n~100 tracks
    Efectividad: ~70-80% en casos típicos
    
    Alternativa futura: MiniZinc CSP solver (scope post-MVP)
    """
    random.seed(seed)
    tracks = search_tracks_by_constraints(constraints)
    
    # 1. Seleccionar track inicial (cercano a BPM min)
    start_track = min(tracks, key=lambda t: abs(t["bpm"] - constraints["bpm_min"]))
    
    playlist = [start_track]
    total_duration = start_track["duration"]
    used_artists = {start_track["artist"]}
    
    # 2. Greedy: agregar tracks que respeten:
    #    - BPM progresión (nunca disminuir)
    #    - Tonalidad armónica (≤1 semitono)
    #    - Sin repetir artista
    #    - Suma a duración exacta
    
    while total_duration < constraints["target_duration"]:
        remaining = constraints["target_duration"] - total_duration
        
        # Buscar candidato
        best_track = None
        for t in tracks:
            if t["artist"] in used_artists:
                continue
            if t["bpm"] < playlist[-1]["bpm"]:  # Progresión
                continue
            if not is_harmonic(t["tonality"], playlist[-1]["tonality"]):
                continue
            if abs(t["duration"] - remaining) < abs((best_track or t)["duration"] - remaining):
                best_track = t
        
        if not best_track:
            # Backtrack: no hay solución exacta
            break
        
        playlist.append(best_track)
        total_duration += best_track["duration"]
        used_artists.add(best_track["artist"])
    
    # 3. Si no alcanzó duración exacta, retornar best-effort
    return {
        "tracks": playlist,
        "total_duration": total_duration,
        "stats": compute_stats(playlist)
    }

def is_harmonic(tonality_a, tonality_b):
    """Verificar que tonalidades están armónicas (≤1 semitono)"""
    semitones = TONALITY_DISTANCES.get((tonality_a, tonality_b), 2)
    return semitones <= 1
```

**Para sprint técnico, considerar:**
- CSP solver (MiniZinc): exacto pero complejo
- Simulated annealing: más flexible, mejor para exploración
- Integer linear programming: overkill para MVP

---

## 📋 Resumen: Archivos a Copiar

| Pieza | Lab | Archivo | Líneas |
|-------|-----|---------|--------|
| **MCP Server** | Lab 03 | `server.py` | ~120 líneas base |
| **Subagente Parser** | Lab 06 | `orquestador.py` | ~80 líneas patrón |
| **Guardrails** | Lab 07 | `guardrails.py` | ~150 líneas |
| **Frenos** | Lab 02 | `reintentos.py` | ~60 líneas |
| **Orquestador** | Lab 06 | `orquestador.py` | ~200 líneas |
| **Compile_playlist** | — | Algoritmo nuevo | ~100 líneas greedy |

**Total estimado:** ~700 líneas de código base (sin comentarios), 70% reutilización.

---

## 🚀 Orden de Implementación

1. **Servidor MCP** (Lab 03): 5 herramientas stub
2. **Guardrails** (Lab 07): entrada + salida validators
3. **Frenos** (Lab 02): retries + timeouts + sesión
4. **Subagente Parser** (Lab 06): delegación a Haiku
5. **Orquestador** (Lab 06): coordinación central
6. **Compile_playlist** (custom): algoritmo NP-hard
7. **Tests**: request_01, request_02, request_03

---

**Status:** ✅ Mapa de referencias completado. Listo para Sprint 1.

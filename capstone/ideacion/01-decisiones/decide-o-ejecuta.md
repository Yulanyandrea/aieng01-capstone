# Decide o Ejecuta: Matriz de Decisiones

**DJ Playlist Generator Agent** - Quién decide qué en cada paso

---

## Matriz Principal

| # | Acción | Quién | Qué pasa si se equivoca | ¿Movible a CÓDIGO? | ¿DE ACUERDO? |
|----|--------|-------|------------------------|-------------------|-------------|
| 1 | **DJ envía solicitud natural** (ej: "45 min, 115→128 BPM, sin repetir") | PERSONA | Agente recibe entrada malformada → parse falla gracefully | N/A (es input) |si |
| 2 | **Parse: Extraer estructura** (duración, BPM, tonalidades, restricciones) | MODELO | Si interpreta mal → Claude entrega constraints incorrectas | ⚠️ Parcialmente: Regex en CÓDIGO para campos obvios, Claude para ambigüedad |si, el modelo debe ser capaz de consulta la base de datos y generar cada playlist|
| 3 | **Detectar ambigüedad crítica** (ej: "90 min" = ¿1 set o 2 fases?) | MODELO | Si adivina → playlist inválida para DJ | ✅ SÍ → `should_detain()` en CÓDIGO: si "min" > 60 Y no menciona "fase", DETIENE |Si |
| 4 | **Decidir: ¿necesita subagent?** (restricciones complejas?) | MODELO | Si no delega → no negocia conflictos | ✅ SÍ → `should_validate_constraints()` en CÓDIGO: regla determinista (fases? no_repeat? custom_max?) |Si |
| 5 | **Invocar Subagent Validator** (si hay conflicto) | CÓDIGO | Subagent falla → constraints no refinadas | Ejecuta en CÓDIGO |Si |
| 6 | **Subagent: Identificar conflictos** (ej: 90 min + 4 artistas = imposible) | MODELO | Si no identifica → sigue con restricciones inviables | ✅ SÍ → Función `check_math_feasibility()` en CÓDIGO: tracks_needed = duration / avg_track_length, artistas_available = distinct(catalog), if tracks_needed > artistas_available → conflict |Si |
| 7 | **Subagent: Proponer 2-3 opciones** | MODELO | Si propone opciones malas → DJ no confía | Parcialmente: opciones hardcodeadas en CÓDIGO, Claude elige cuál presentar |Si |
| 8 | **Refinar constraints** (adoptar ajuste de subagent) | CÓDIGO | Si no aplica → sigue con restricciones originales | Ejecuta en CÓDIGO |Si |
| 9 | **Consultar MCP: validate_feasibility()** | CÓDIGO | Si falla → no sabe si es viable | Ejecuta en CÓDIGO | |
| 10 | **Decisión: ¿procede o pide ajuste?** | MODELO | Si procede sin viabilidad → alucinación | ✅ SÍ → CÓDIGO chequea: if not viable → return error, no continue |si, el modelo no debe alucinar e inventar datos o reglas que no están explicitas |
| 11 | **MCP: search_tracks()** (por criterios BPM/tonalidad) | CÓDIGO | Si retorna vacío → no hay tracks | Ejecuta en CÓDIGO |Si |
| 12 | **Build: Algoritmo greedy** (progresión BPM, compatibilidad armónica) | CÓDIGO | Si falla → playlist incoherente | Ejecuta en CÓDIGO (es algoritmo puro) |Si, el codigo debe determinar la compatibilidad armonica de cada playlist |
| 13 | **Validar playlist interna** (¿duración ~45 min? ¿BPM progresa?) | CÓDIGO | Si no valida → envía basura | ✅ SÍ → CÓDIGO chequea: duration 45±1, bpm_start < bpm_end, no artistas repetidos |si, el codigo debe revisar que los parametros se cumplan|
| 14 | **Generar explicación por pista** | MODELO | Si explica mal → DJ no entiende decisión | Parcialmente: template en CÓDIGO, Claude personaliza |si, claude debe explicar su decisión y si se ajusta con los parametros que pide el DJ |
| 15 | **Armar JSON final** | CÓDIGO | Si JSON malformado → DJ no puede parsear | Ejecuta en CÓDIGO (serialize con validación schema) | |
| 16 | **Checkpoint humano: DJ revisa** | PERSONA | Si DJ no aprueba → se aborta | N/A (es decisión humana) | |
| 17 | **Si DJ rechaza: Retornar y pedir ajustes** | MODELO | Si no captura feedback → falla iteración | ✅ SÍ → CÓDIGO gestiona reintentos: max 3, timeout 5 min total |si, el codigo debe reintentar |
| 18 | **Si DJ aprueba: Retornar playlist** | CÓDIGO | Si retorna mientras DJ aún decidiendo → race condition | ✅ SÍ → CÓDIGO espera confirmación explícita antes de retornar |si |

---

## Detalle: Decisiones que DEBEN moverse a CÓDIGO

### 1️⃣ **Detectar ambigüedad crítica** (Row 3)
**Actual:** Claude adivina si "90 min" = 1 set o 2 fases  
**Propuesto:**
```python
def should_detain_for_clarification(constraints: ParsedConstraints) -> bool:
    """
    Detiene si hay ambigüedad crítica que afecta playlist.
    Regla: Si duración > 60 min Y no menciona "fase/set" → DETIENE
    """
    return (
        constraints.duration_minutes > 60 and 
        constraints.phases is None
    )

# En agent:
if should_detain_for_clarification(parsed):
    return "⚠️ ¿90 minutos = 1 set o 2 fases de 45 cada una?"
```

**Por qué:** Cálculo de lógica pura, no requiere LLM.

---

### 2️⃣ **Decidir si necesita subagent** (Row 4)
**Actual:** Claude decide implícitamente  
**Propuesto:**
```python
def should_validate_constraints(constraints: ParsedConstraints) -> bool:
    """
    Heurística determinista: ¿restricciones son complejas?
    Justificación: Evitar overhead LLM para casos simples.
    """
    return (
        constraints.phases is not None or           # Multi-fase
        constraints.no_artist_repeat or             # Sin repetir
        constraints.max_artist_repeats < 999        # Restricción custom
    )

# En agent:
if should_validate_constraints(parsed):
    invoke_subagent_validator()
```

**Por qué:** Heurística determinista, no ambigua, reutilizable.

---

### 3️⃣ **Identificar conflicto matemático** (Row 6)
**Actual:** Subagent Claude lo intuye  
**Propuesto:**
```python
def calculate_feasibility(
    duration_min: int,
    bpm_range: tuple,
    tonalities: list,
    no_artist_repeat: bool,
    catalog_stats: dict
) -> dict:
    """
    Cálculo puro: ¿es posible?
    
    Inputs:
      - duration_min: minutos solicitados
      - catalog_stats: {total_tracks, unique_artists, tracks_by_bpm_range, ...}
    
    Output:
      {
        "feasible": bool,
        "tracks_needed": int,
        "tracks_available": int,
        "artists_needed": int,
        "artists_available": int,
        "conflict": str or None
      }
    """
    avg_track_length = 5.8  # minutos (constante)
    tracks_needed = int(duration_min / avg_track_length) + 1
    
    tracks_in_range = catalog_stats["tracks_in_bpm_range"]
    artists_in_range = catalog_stats["unique_artists_in_range"]
    
    if no_artist_repeat and tracks_needed > artists_in_range:
        return {
            "feasible": False,
            "tracks_needed": tracks_needed,
            "tracks_available": len(tracks_in_range),
            "artists_needed": tracks_needed,
            "artists_available": artists_in_range,
            "conflict": f"Necesitas {tracks_needed} tracks sin repetir, "
                       f"pero solo hay {artists_in_range} artistas disponibles"
        }
    
    if tracks_needed > len(tracks_in_range):
        return {
            "feasible": False,
            "conflict": f"Necesitas ~{tracks_needed} tracks, "
                       f"pero solo hay {len(tracks_in_range)} disponibles"
        }
    
    return {"feasible": True}
```

**Por qué:** Cálculo con números (5.8 min, duración, cantidad). Nunca va en LLM.

---

### 4️⃣ **Validar playlist interna** (Row 13)
**Actual:** Claude asume que build_playlist() es correcto  
**Propuesto:**
```python
def validate_playlist(
    playlist: list,
    constraints: ParsedConstraints
) -> dict:
    """
    Guardrail: ¿playlist respeta restricciones?
    
    Checks:
    1. Duración: target ± 1 min
    2. BPM: bpm_start ≤ todos ≤ bpm_end
    3. Artistas: no repetidos (si restricción)
    """
    total_duration = sum(t["duration"] for t in playlist) * 60
    target_duration = constraints.duration_minutes * 60
    
    errors = []
    
    if abs(total_duration - target_duration) > 60:  # ±1 min
        errors.append(
            f"Duración fuera de rango: {total_duration/60:.1f} min "
            f"(esperado: {constraints.duration_minutes}±1)"
        )
    
    bpms = [t["bpm"] for t in playlist]
    if not all(constraints.bpm_start <= bpm <= constraints.bpm_end 
               for bpm in bpms):
        errors.append(f"BPM fuera de rango: {min(bpms)}-{max(bpms)}")
    
    if constraints.no_artist_repeat:
        artists = [t["artist"] for t in playlist]
        if len(artists) != len(set(artists)):
            errors.append("Artistas repetidos (violó restricción no_artist_repeat)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "stats": {
            "total_duration": total_duration / 60,
            "bpm_range": (min(bpms), max(bpms)) if bpms else (0, 0),
            "unique_artists": len(set(a["artist"] for a in playlist))
        }
    }
```

**Por qué:** Validación es lógica pura, no decisión creativa. Evita sorpresas.

---

### 5️⃣ **Gestionar reintentos** (Row 17)
**Actual:** Claude maneja reintentos implícitamente  
**Propuesto:**
```python
class RetryPolicy:
    MAX_ATTEMPTS = 3
    TIMEOUT_TOTAL = 5 * 60  # 5 minutos
    TIMEOUT_PER_ATTEMPT = 120  # 2 minutos por request

def run_with_retry(
    agent_fn,
    dj_request,
    retry_policy: RetryPolicy = RetryPolicy()
) -> str:
    """Ejecuta agent con reintentos automáticos."""
    attempts = 0
    start_time = time.time()
    
    while attempts < retry_policy.MAX_ATTEMPTS:
        elapsed = time.time() - start_time
        if elapsed > retry_policy.TIMEOUT_TOTAL:
            raise TimeoutError(f"Tiempo total excedido: {elapsed:.0f}s")
        
        try:
            return agent.run(dj_request)
        except Exception as e:
            attempts += 1
            if attempts >= retry_policy.MAX_ATTEMPTS:
                raise
            print(f"Intento {attempts} falló, reintentando...")
            time.sleep(1)
```

**Por qué:** Números (max intentos, timeout, espera). Nunca va en LLM.

---

## Resumen: Qué va en CÓDIGO

| Tipo | Ejemplo | Por qué |
|------|---------|--------|
| **Cálculos numéricos** | tracks_needed = duration / 5.8 | Determinista, verificable |
| **Comparaciones** | if no_artist_repeat and needed > available | Lógica binaria |
| **Validaciones** | if duration > target±60s → error | Guardrail |
| **Límites** | max_attempts = 3, timeout = 5min | Presupuesto |
| **Rutas** | if ambiguo → detén, else → continúa | Decisión determinista |
| **Reintentos** | while attempts < 3 | Política |

---

## Conclusión

La tabla anterior es tu **mapa de quién decide qué**. Las sugerencias de "movible a CÓDIGO" son:
- **✅ SÍ:** Hazlo. Es lógica pura, guardrail o presupuesto.
- **⚠️ Parcialmente:** Claude elige entre opciones en CÓDIGO.
- **N/A:** Déjalo en MODELO o PERSONA.

Esto hace tu sistema:
- **Predecible:** Reglas claras y ejecutables.
- **Auditable:** Se ve exactamente qué se chequea.
- **Escalable:** Agregar restricción = 1 línea en guardrail.

---

Co-Authored-By: Claude Code <noreply@anthropic.com>

# Decisiones de Diseño - DJ Playlist Generator

## 1. Herramienta para el Catálogo

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| **API Spotify** | Real, datos actualizados, metadatos completos | Requiere autenticación, límites de rate, latencia |
| **Base de datos local (SQLite)** | Rápido, sin dependencias externas, control total | Requiere pre-cargar datos, datos estáticos |
| **Mock (datos simulados)** | Prototipado rápido, sin dependencias | No realista, limitado |

**Elegida:** Mock para MVP + plan para migrar a SQLite
**Por qué:** Podemos testear la lógica del agente sin complejidad externa. Luego escalamos.

---

## 2. Tipo de Agente

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| **Agentic loop** (iterativo con retroalimentación) | Puede corregir errores, consulta en caso de ambigüedad | Complejo, múltiples llamadas LLM |
| **Multi-step prompt** (secuencia de pasos determinista) | Rápido, predecible, bajo costo | Menos flexible ante entradas varias |
| **Subagente especializado** | Modular, reutilizable | Overhead, complejidad |

**Elegida:** Multi-step prompt + herramientas de validación
**Por qué:** Las restricciones DJ son complejas pero predecibles. Un flujo paso-a-paso es suficiente. Si falla, el DJ ve claramente por qué.

---

## 3. Control de Restricciones

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| **Verificación estricta** | Garantiza salida válida o error claro | Puede rechazar solicitudes válidas por detalles |
| **Best-effort** (best fit) | Flexible, siempre entrega algo | Puede violar restricciones sin avisar |
| **Iterativa** (agente ajusta) | Flexible + controlada | Lento, muchas llamadas |

**Elegida:** Verificación estricta + fallback best-effort con advertencias
**Por qué:** El DJ necesita saber si su solicitud es viable o no. Si no cabe exacto, le decimos qué se relaja.

---

## 4. Flujo Principal del Agente

```
INPUT (Solicitud DJ)
  ↓
PARSING: Extraer restricciones estructuradas
  ↓
VALIDACIÓN: ¿Catálogo puede cumplir?
  ├─ Sí → GENERACIÓN
  └─ No → ERROR + Sugerencias
  ↓
GENERACIÓN: Build playlist con algoritmo
  ├─ Progresión BPM
  ├─ Compatibilidad armónica
  ├─ Sin repeticiones
  └─ Duraciones exactas
  ↓
OUTPUT: Playlist + Explicación por pista
```

---

## 5. Herramientas que Usará el Agente

1. **parse_constraints()** → Estructura vaga → Restricciones claras
2. **validate_feasibility()** → ¿Es posible? Sí/No + razón
3. **search_tracks()** → BPM/Tonalidad/Artista → Tracks
4. **build_playlist()** → Greedy algorithm respetando restricciones
5. **explain_choices()** → Por cada pista, explicación

---

## 6. Parámetros del Mock Catálogo

- **Tracks:** ~100 simuladas (reducido pero suficiente para testing)
- **Metadatos:** `{id, artist, title, bpm, tonality, duration, genre, mood}`
- **Tonalidades:** Do Mayor, Re Mayor, ... La Menor (compatibilidad = mismo centro o relativo)
- **Géneros:** House, Tech House, Deep House, Techno


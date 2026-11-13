# 📋 Resumen de Entrevista - Tu Visión del Agente

Estas son tus respuestas. Claude Code las lee cada vez que arranque aquí.

---

## Tu Frase (La Promesa)

> **"Dado una solicitud de DJ en chat interactivo, mi agente produce 1 JSON con playlists validadas, y sé que funciona porque: duración = exacta, tonalidades = concuerdan, artistas = sin repetir en su fase."**

---

## Tu Línea Roja (Decisiones que NO toma Claude)

| # | Decisión | Quién Decide | Por qué |
|---|----------|--------------|--------|
| 1 | Ambigüedad (90 min = 1 o 2 sets?) | **DJ** | Evita asumir |
| 2 | Catálogo insuficiente | **Agente** (best-effort) | Nunca rechaza |
| 3 | Aprobación final de playlist | **DJ** (checkpoint) | Control humano |
| 4 | Urgencia imposible (< 2 min) | **Agente** (advierte) | No bajo presión |

---

## P1: Caso Más Importante

**Tu respuesta:** `request_03_complex.txt` (Alex, 90 min, 2 fases)

**Por qué:** Reglas claras, complejo, multi-compilación. Esto es tu golden set.

---

## P2: Cómo Manejar 90 Minutos

**Tu respuesta:** Opción C - **Agente DETIENE y pide confirmación**

```
DJ: "90 minutos"
Agente: "¿Genero 1 set de 90 min o 2 sets de 45 + 45?"
DJ: Elige
Agente: Procede
```

---

## P3: El Peor Día Malo

**Tu respuesta:** Opción C - **Urgencia imposible**

- Ejemplo: "Necesito esto en 30 segundos"
- Problema: No hay tiempo para consultar catálogo (mínimo viable = 2 min)
- Reacción: Agente advierte, no ejecuta bajo presión

---

## P4: Formato de Salida

**Tu respuesta:** 1 archivo JSON con 2 fases

```json
{
  "phase_1": [
    { "id": 1, "artist": "...", "bpm": 110, "tonality": "A_minor", ... },
    { "id": 2, "artist": "...", "bpm": 112, "tonality": "E_minor", ... }
  ],
  "phase_2": [
    { "id": 10, "artist": "...", "bpm": 120, "tonality": "C_major", ... },
    { "id": 11, "artist": "...", "bpm": 125, "tonality": "G_major", ... }
  ]
}
```

---

## P5: Datos del Catálogo

**Tu respuesta:** 
- **Fuente:** Mock (MVP). Escalable a SQLite después.
- **Campos imprescindibles:** `bpm` + `tonality` (de ahí todo)
- **Otros:** artista, duración, género, mood, id

**Por qué:** BPM y tonalidad determinan la duración total del set.

---

## P6: Golden Set (Cómo Verificar que Funciona)

**Tu respuesta:** Para `request_03` (Alex, 2 fases), FUNCIONA si:

✅ **Duración exacta:**
- Fase 1: 45±1 minutos
- Fase 2: 45±1 minutos

✅ **Tonalidades correctas:**
- Fase 1: Solo tonalidades menores (A_minor, E_minor, etc.)
- Fase 2: Solo tonalidades mayores (C_major, G_major, etc.)

✅ **Sin repeticiones:**
- Ningún artista repetido DENTRO de su fase
- (Pero sí puede aparecer en ambas fases)

✅ **Salida:**
- JSON con ambas fases
- Explicación por pista
- Estadísticas

---

## P7: Entrada del DJ

**Tu respuesta:** Chat interactivo + DJ decide cuándo lanzar

```
DJ: "Necesito 90 minutos..."
Agente: [procesa]
DJ: [revisa]
DJ: "Apruebo" ✅
Agente: [genera JSON]
```

**NO:** Pegar archivos. **SÍ:** Chat natural.

---

## P8: Día Malo - Catálogo Insuficiente

**Tu respuesta:** Best-effort, nunca rechaza

Ejemplo: DJ pide 90 min sin repetir artistas, pero hay pocos tracks.

Agente:
- Genera lo que puede (ej: 65 min en lugar de 90)
- Avisa: "⚠️ Tuve que repetir 2 artistas en fase 2"
- DJ decide si acepta o relaja restricción

---

## P9: Aprobación Humana

**Tu respuesta:** OBLIGATORIA antes de generar JSON final

```
Agente propone: "Aquí está tu playlist. Valida:"
DJ ve: Duraciones, tonalidades, artistas
DJ aprueba ✅ o rechaza ❌
Solo después de ✅ → JSON final
```

---

## Resumen de Flujo

```
1. DJ chat: "90 min, fase 1 tonos menores, fase 2 mayores"
2. Agente: "¿1 set o 2 sets?" → DJ decide
3. Agente: Busca en catálogo (BPM + tonalidad)
4. Agente: Si insuficiente → best-effort + aviso
5. Agente: Propone playlist (preview)
6. DJ: Valida y aprueba ✅
7. Agente: Genera 1 JSON final con ambas fases
```

---

## Lo Que NO Toma Claude

- ✋ No decide si 90 min = 1 o 2 sets
- ✋ No aprueba la playlist final
- ✋ No ejecuta bajo urgencia imposible
- ✋ No rechaza por catálogo insuficiente (best-effort)

---

**Fecha:** 2026-11-11  
**Entrevistador:** Claude Code  
**Estado:** ✅ Definición completa, lista para implementar

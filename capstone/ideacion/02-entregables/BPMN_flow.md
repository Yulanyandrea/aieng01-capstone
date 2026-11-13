# BPMN - DJ Playlist Generator Workflow

## Flujo del Agente

```
┌─────────────────────────────────────────────────────────────────┐
│                    DJ REQUEST RECEIVED                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  PARSING & VALIDATION LAYER    │
        │  - Extract constraints         │
        │  - Normalize BPM/tonos/duración│
        └────────────┬───────────────────┘
                     │
          ┌──────────▼──────────┐
          │  Constraints        │
          │  Parseable?         │
          └──────────┬──────────┘
                     │
        ┌────────────┴────────────┐
        │ Sí                  No  │
        ▼                         ▼
    ┌─────────┐          ┌──────────────┐
    │ Continue│          │ ERROR RETURN │
    └────┬────┘          │ + Suggestion │
         │               └──────────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │ FEASIBILITY CHECK            │
    │ - ¿Catálogo cubre BPM range? │
    │ - ¿Tonos armónicos?          │
    │ - ¿Duración cabe?            │
    └────────────┬─────────────────┘
                 │
         ┌───────▼───────┐
         │ Possible?     │
         └───────┬───────┘
                 │
    ┌────────────┴────────────┐
    │ Sí                  No  │
    ▼                         ▼
┌──────────┐         ┌──────────────────┐
│ Continue │         │ PARTIAL SOLUTION │
└────┬─────┘         │ (relax constraints)
     │               │ OR ERROR
     │               └──────────────────┘
     │
     ▼
┌────────────────────────────────┐
│ GENERATION ALGORITHM           │
│ 1. Start track (closest BPM)  │
│ 2. Greedy search next track   │
│    - BPM progression           │
│    - Harmonic compatibility    │
│    - No artist repeat          │
│ 3. Fill until duration         │
└────────────┬───────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ PLAYLIST GENERATED │
    └────────────┬───────┘
                 │
                 ▼
    ┌──────────────────────────────┐
    │ EXPLANATION BUILDER          │
    │ - Why each track here?       │
    │ - BPM transition             │
    │ - Harmonic reasoning         │
    └────────────┬─────────────────┘
                 │
                 ▼
         ┌──────────────────┐
         │ OUTPUT           │
         │ - Playlist JSON  │
         │ - Explanation    │
         │ - Stats (total   │
         │   BPM range,     │
         │   duration)      │
         └──────────────────┘
```

## Puntos de Decisión Clave

| Nodo | Entrada | Salida OK | Salida ERROR |
|------|---------|-----------|--------------|
| Parseable? | Texto libre del DJ | Estructura normalizada | Solicitud ambigua, rechazar |
| Possible? | Restricciones + Catálogo | Proceder generación | Catálogo insuficiente, sugerir relajación |
| Duration reached? | Algoritmo greedy | Playlist completa | (No aplica, algoritmo itera) |

## Flujo Alternativo: Best-Effort

Si `Possible? = No`, ofrecer modo degradado:
- Relax duración ±5%
- Relax compatibilidad armónica (permitir relativos)
- Permitir 1 artista repetido máximo
- Avisar todas las relajaciones


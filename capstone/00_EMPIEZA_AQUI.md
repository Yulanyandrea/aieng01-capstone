# 🎵 DJ Playlist Generator — Comienza Aquí

## ¿Qué Acabamos de Hacer?

**Entrevista + Visión Definida** de tu agente DJ. Ahora sabe exactamente qué construir.

```
Tu solicitud → Agente Chat → DJ Aprueba ✅ → JSON Playlists
```

---

## 📖 Lee Esto Primero (En Este Orden)

### 1️⃣ TU VISIÓN (2 min)
[TU_VISION.txt](TU_VISION.txt)
- La promesa del agente
- Las 4 líneas rojas (decisiones que NO toma Claude)
- Golden set (caso crítico)

### 2️⃣ RESPUESTAS COMPLETAS (5 min)
[ENTREVISTA_RESUMEN.md](ENTREVISTA_RESUMEN.md)
- Tus 9 respuestas a la entrevista
- Por qué cada decisión
- Flujo completo

### 3️⃣ CONTEXTO TÉCNICO (10 min)
[CLAUDE.md](CLAUDE.md)
- Definición formal del agente
- Entrada → Procesamiento → Checkpoint → Salida
- Golden set detallado (cómo verificar que funciona)

---

## 🎯 Lo Más Importante

### La Promesa
> "Dado una solicitud de DJ en chat interactivo, produzco 1 JSON con playlists validadas. Funciona si: duración=exacta, tonalidades=concuerdan, artistas=sin repetir en su fase."

### Las 4 Líneas Rojas
| Decisión | Quién Decide |
|----------|--------------|
| Ambigüedad (90 min = 1 o 2 sets?) | **DJ** |
| Catálogo insuficiente | **Agente** (best-effort) |
| Aprobación final | **DJ** (checkpoint) |
| Urgencia imposible | **Agente** (advierte) |

### El Golden Set
**`request_03_complex.txt` (Alex, 90 min, 2 fases)**

✅ FUNCIONA SI:
- Fase 1: 45±1 min, BPM 110-120, tonos MENORES, sin artistas repetidos
- Fase 2: 45±1 min, BPM 120-130, tonos MAYORES, sin artistas repetidos
- JSON con ambas fases + explicación

---

## 📊 Estructura del Proyecto

```
capstone/
├── 00_EMPIEZA_AQUI.md ← Tú estás aquí
│
├── 📄 Tu Visión
│   ├── TU_VISION.txt (visual)
│   ├── ENTREVISTA_RESUMEN.md (respuestas)
│   └── CLAUDE.md (definición técnica)
│
├── 📄 Documentación Anterior (MVP)
│   ├── README.md
│   ├── INICIO_RAPIDO.md
│   ├── INDEX.md
│   └── ...
│
├── 🐍 Código
│   ├── dj_agent.py (agente actual)
│   ├── run_all_tests.py
│   └── venv/
│
└── 📁 ideacion/
    ├── 00-material/ (casos de entrada)
    ├── 01-decisiones/ (matriz decisiones)
    └── 02-entregables/ (BPMN + ejemplos)
```

---

## 🚀 Próximos Pasos

### Fase 1: Implementar Chat Interactivo
El agente actual es MVP. Ahora necesita:
- ✅ Chat interactivo (no archivos)
- ✅ Checkpoint humano (DJ aprueba antes de JSON)
- ✅ Manejo de ambigüedad (90 min = 1 o 2 sets)

### Fase 2: Validar Golden Set
Asegurar que `request_03_complex.txt` funciona perfectamente:
- Duración exacta cada fase
- Tonalidades correctas
- Sin artistas repetidos en su fase

### Fase 3: Best-Effort
Si catálogo insuficiente, generar lo que se pueda + avisos claros.

---

## 📞 Referencia Rápida

| Pregunta | Ver |
|----------|-----|
| ¿Cuál es tu visión? | [TU_VISION.txt](TU_VISION.txt) |
| ¿Cómo responde el agente cada escenario? | [ENTREVISTA_RESUMEN.md](ENTREVISTA_RESUMEN.md) |
| ¿Cuáles son los detalles técnicos? | [CLAUDE.md](CLAUDE.md) |
| ¿Cómo ejecuto el MVP actual? | [INICIO_RAPIDO.md](INICIO_RAPIDO.md) |
| ¿Cuál es la arquitectura completa? | [README.md](README.md) |

---

## ✅ Checklist Entrevista

- [x] P1: Caso más importante = request_03 (2 fases)
- [x] P2: Ambigüedad → DJ decide
- [x] P3: Peor día = urgencia imposible (< 2 min)
- [x] P4: Salida = 1 JSON con 2 fases
- [x] P5: Datos = Mock (campos clave: BPM + tonality)
- [x] P6: Golden set = duración exacta + tonalidades + sin repeticiones
- [x] P7: Entrada = chat interactivo, DJ decide cuándo lanzar
- [x] P8: Catálogo insuficiente = best-effort, nunca rechaza
- [x] P9: Aprobación humana = OBLIGATORIA antes de JSON final

---

## 📌 Estado

```
MVP Anterior: ✅ Funcional (dj_agent.py, mock catalog)
Tu Visión: ✅ Definida (CLAUDE.md actualizado)
Próximo: 🚀 Implementar chat interactivo + checkpoint
```

---

**Fecha:** 2026-11-11  
**Entrevistador:** Claude Code  
**Próxima Reunión:** Después de implementar chat + checkpoint + validar golden set

🎵 **Listo para construir lo que realmente necesitas.**

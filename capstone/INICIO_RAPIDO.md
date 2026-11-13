# 🚀 Inicio Rápido - DJ Playlist Generator

## 5 Minutos para Empezar

### 1. Activar el entorno (necesario solo una vez)

```bash
cd /workshop/capstone
python3 -m venv venv
source venv/bin/activate
pip install anthropic -q
```

### 2. Ejecutar los tests

```bash
# Opción A: Todos los 3 casos
python run_all_tests.py

# Opción B: Solo el caso limpio
python dj_agent.py
```

### 3. Ver tu resultado

El agente imprimirá:
- 🎤 La solicitud del DJ
- 🔧 Las herramientas que usa
- 📋 La playlist generada
- ✅ Explicación por pista

---

## 📚 Documentación

| Archivo | Para qué |
|---------|----------|
| [README.md](README.md) | Guía completa + arquitectura |
| [CLAUDE.md](CLAUDE.md) | Contexto del proyecto |
| [ideacion/01-decisiones/decisiones.md](ideacion/01-decisiones/decisiones.md) | Tabla de decisiones |
| [ideacion/02-entregables/BPMN_flow.md](ideacion/02-entregables/BPMN_flow.md) | Diagrama del flujo |
| [ideacion/02-entregables/EJEMPLO_SALIDA.md](ideacion/02-entregables/EJEMPLO_SALIDA.md) | Output esperado |
| [PROYECTO_COMPLETADO.md](PROYECTO_COMPLETADO.md) | Resumen final |

---

## 🎯 Casos de Prueba

### ✅ Test 1: Solicitud Limpia
```
DJ: María | 45 min | 115→128 BPM | Do Mayor | Sin artistas repetidos
```
→ Genera playlist directamente

### ⚠️ Test 2: Solicitud Vaga
```
DJ: Carlos | 1 hora | 120-130 | "tonos veraniegos" | Urgente (10 min!)
```
→ Agente parsea e interpreta

### 🎯 Test 3: Multi-fase
```
DJ: Alex | 90 min en 2 fases | 110-120 (menores) + 120-130 (mayores)
```
→ Agente splitea en 2 playlists

---

## 🔧 Personalizar

Edita el final de `dj_agent.py`:

```python
request = """
DJ: TuNombre
Duración: 60 minutos
BPM: 120 a 130
Tonos: Sol Mayor
Restricción: Sin repetir artistas
Género: Techno
"""

agent.run(request)
```

Guarda y ejecuta:
```bash
python dj_agent.py
```

---

## ❓ Troubleshooting

**Error: "anthropic module not found"**
```bash
source venv/bin/activate
pip install anthropic
```

**Error: "403 - key not allowed to access model"**
→ Tu API key solo accede a `bedrock-claude-sonnet` (ya configurado)

**Agente tarda mucho**
→ Es normal (Claude thinking). Espera 10-30 segundos.

---

## 📊 Estructura Rápida

```
capstone/
├── dj_agent.py          ← El agente (ejecutable)
├── run_all_tests.py     ← Tests (ejecutable)
├── ideacion/
│   ├── 00-material/     ← Casos de entrada
│   ├── 01-decisiones/   ← Decisiones + matriz
│   └── 02-entregables/  ← BPMN + ejemplos
└── README.md            ← Guía completa
```

---

## ✅ Próximo Paso

```bash
python dj_agent.py
```

¡Eso es todo! El agente hará el resto. 🎵


# 💾 Backup & Restore - DJ Playlist Generator

**Creado:** 2026-11-11  
**Archivo:** `capstone-backup-20261111-021526.tar.gz` (ubicación: `/workshop/`)

---

## Cómo hacer backup ahora

### Opción 1: Tar (Linux/Mac)
```bash
cd /workshop
tar --exclude='capstone/venv' --exclude='capstone/__pycache__' --exclude='*.pyc' \
    -czf capstone-backup-$(date +%Y%m%d-%H%M%S).tar.gz capstone/
```

### Opción 2: Zip (si tienes zip)
```bash
cd /workshop
zip -r capstone-backup-$(date +%Y%m%d).zip capstone/ \
    -x "capstone/venv/*" "capstone/__pycache__/*" "*.pyc"
```

### Opción 3: Manual (copiar archivos clave)
```bash
# Copiar solo lo importante (sin venv)
cp -r /workshop/capstone /tmp/capstone-backup
rm -rf /tmp/capstone-backup/venv
tar -czf /tmp/capstone-backup.tar.gz /tmp/capstone-backup
```

---

## Qué se incluye en el backup

✅ **SE INCLUYE:**
- ✓ Todos los archivos `.py` (código)
- ✓ Todos los archivos `.md` (documentación)
- ✓ Carpeta `ideacion/` (análisis y decisiones)
- ✓ `run_all_tests.py` (tests)

❌ **SE EXCLUYE:**
- ✗ `venv/` (entorno virtual, ocupa 500MB)
- ✗ `__pycache__/` (compilados, se regeneran)
- ✗ `.git/` (si existe)
- ✗ `*.pyc` (bytecode)

**Tamaño:** ~47 KB (sin venv)

---

## Cómo restaurar el backup

### Si el workspace se pierde y tienes el .tar.gz:

```bash
# 1. Descargar/obtener el archivo capstone-backup-*.tar.gz

# 2. Extraerlo
cd /workshop
tar -xzf capstone-backup-20261111-021526.tar.gz

# 3. Reinstalar venv y dependencias
cd capstone
python3 -m venv venv
source venv/bin/activate
pip install anthropic

# 4. Verificar que funciona
python3 run_all_tests.py
```

---

## Checklist post-restauración

- [ ] Backup extraído en `/workshop/capstone/`
- [ ] `venv/` creado y activado
- [ ] `pip install anthropic` completado
- [ ] `python3 run_all_tests.py` ejecuta sin errores
- [ ] Ver 4/4 tests pasando

---

## Archivos críticos a guardar

Si solo quieres guardar lo esencial (código + docs):

```bash
# Código
- dj_agent.py
- catalog_mcp_server.py
- constraint_validator_agent.py
- run_all_tests.py

# Documentación crítica
- CLAUDE.md
- JUSTIFICATION.md
- ARCHITECTURE.md
- ideacion/01-decisiones/decide-o-ejecuta.md

# Casos de prueba
- ideacion/00-material/request_*.txt
```

---

## Estrategia de backup recomendada

**Diario:**
```bash
# Al final de cada sesión
tar -czf ~/capstone-$(date +%Y%m%d).tar.gz /workshop/capstone/ \
    --exclude='capstone/venv' --exclude='__pycache__'
```

**GitHub (recomendado):**
```bash
cd /workshop/capstone
git init
git add .
git commit -m "DJ Playlist Generator v1.1"
git remote add origin <tu-repo>
git push -u origin main
```

---

## Recuperación de emergencia

Si pierdes todo:

1. **Tienes el .tar.gz:**
   ```bash
   tar -xzf capstone-backup-*.tar.gz
   cd capstone
   python3 -m venv venv
   source venv/bin/activate
   pip install anthropic
   python3 run_all_tests.py
   ```

2. **No tienes el .tar.gz pero recuerdas estructura:**
   - Lee CLAUDE.md → Entiendes qué es
   - Lee JUSTIFICATION.md → Entiendes por qué
   - Lee decide-o-ejecuta.md → Entiendes flujo
   - Recrea archivos .py según ARCHITECTURE.md

3. **Último recurso (GitHub):**
   ```bash
   git clone <tu-repo>
   cd capstone
   python3 -m venv venv && source venv/bin/activate && pip install anthropic
   python3 run_all_tests.py
   ```

---

## Tamaños típicos

| Elemento | Tamaño | Incluido |
|----------|--------|----------|
| Código (.py) | ~50 KB | ✓ |
| Documentación (.md) | ~200 KB | ✓ |
| ideacion/ | ~50 KB | ✓ |
| venv/ | ~500+ MB | ✗ |
| __pycache__/ | ~5 MB | ✗ |
| **Total con backup** | **~300 KB** | |
| **Total con venv** | **~600+ MB** | |

---

## Ubicación actual del backup

```
/workshop/capstone-backup-20261111-021526.tar.gz
```

**Para descargar:** Descarga este archivo del workspace.

---

Co-Authored-By: Claude Code <noreply@anthropic.com>

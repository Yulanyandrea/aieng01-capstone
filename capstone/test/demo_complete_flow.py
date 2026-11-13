#!/usr/bin/env python3
"""
DEMO COMPLETO: Solicitud DJ → Propuesta → Aprobación → Finalize → JSON FINAL
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentes.dj_agent import DJPlaylistAgent
from proposal_storage import ProposalStorage
from checkpoint_server import app
import json

print("\n" + "=" * 80)
print("🎵 DJ PLAYLIST GENERATOR - COMPLETE WORKFLOW DEMO")
print("=" * 80)

# Setup
ProposalStorage.clear_all()
app.config['TESTING'] = True
client = app.test_client()

# ============================================================================
# PASO 1: DJ SOLICITA PLAYLIST
# ============================================================================
print("\n" + "█" * 80)
print("PASO 1️⃣ : DJ SOLICITA PLAYLIST")
print("█" * 80)

agent = DJPlaylistAgent()
agent.dj_email = "dj_test@local"
agent.user_id = "dj_test"

request_text = """DJ: TestDJ
Duración: 45 minutos
BPM: 120 a 128
Tonalidades: C Mayor, G Mayor
Restricción: Máximo 2 artistas repetidos
Género: House"""

print(f"\n🎤 Solicitud:\n{request_text}")
print("\n⏳ Procesando con agente...")

agent.run(request_text)

# ============================================================================
# PASO 2: OBTENER PROPUESTA GUARDADA
# ============================================================================
print("\n" + "█" * 80)
print("PASO 2️⃣ : OBTENER PROPUESTA GUARDADA")
print("█" * 80)

proposals = ProposalStorage.list_proposals_by_dj("dj_test@local")
if not proposals:
    print("❌ No se generó propuesta")
    exit(1)

prop = proposals[0]
proposal_id = prop["proposal_id"]
print(f"\n✅ Propuesta: {proposal_id}")
print(f"   Status: {prop['status']}")
print(f"   Tracks: {len(prop.get('playlist_tracks', []))} tracks")

# ============================================================================
# PASO 3: PM APRUEBA PROPUESTA
# ============================================================================
print("\n" + "█" * 80)
print("PASO 3️⃣ : PM APRUEBA PROPUESTA VÍA HTTP")
print("█" * 80)

# Obtener propuesta completa
proposal = ProposalStorage.get_proposal(proposal_id)
print(f"\n📍 Aprobando con token: {proposal.approval_token[:20]}...")

# Simular POST a checkpoint endpoint
response = client.post(
    f'/checkpoint/{proposal_id}/approve',
    json={"feedback": "Perfect for the 11pm slot!"}
)

if response.status_code == 200:
    print(f"✅ Propuesta aprobada exitosamente")
    status = ProposalStorage.get_status(proposal_id)
    print(f"   Nuevo status: {status['status']}")
    print(f"   Aprobada en: {status['approved_at']}")
else:
    print(f"❌ Error: {response.get_json()}")
    exit(1)

# ============================================================================
# PASO 4: FINALIZE - GENERAR JSON FINAL
# ============================================================================
print("\n" + "█" * 80)
print("PASO 4️⃣ : FINALIZE - GENERAR JSON FINAL")
print("█" * 80)

response = client.post(f'/finalize/{proposal_id}')

if response.status_code == 200:
    final_json = response.get_json()
    print(f"\n✅ JSON generado exitosamente")
    print(f"   Status: {final_json['status']}")
    print(f"   DJ: {final_json['dj']}")
    print(f"   Tracks: {len(final_json['tracks'])}")
    print(f"   Duration: {final_json['duration']:.1f} min")
    print(f"   BPM range: {final_json['bpm_range']['min']} → {final_json['bpm_range']['max']}")
    print(f"   Aprobada en: {final_json['approved_at']}")
    print(f"   Finalizada en: {final_json['finalized_at']}")

    # ========================================================================
    # PASO 5: PRETTY PRINT JSON FINAL
    # ========================================================================
    print("\n" + "█" * 80)
    print("PASO 5️⃣ : JSON FINAL (LISTO PARA REPRODUCIR)")
    print("█" * 80)

    print("\n" + json.dumps(final_json, indent=2, ensure_ascii=False))
else:
    print(f"❌ Error: {response.get_json()}")
    exit(1)

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("\n" + "=" * 80)
print("✅ WORKFLOW COMPLETO EXITOSO")
print("=" * 80)
print(f"""
Resumen del flujo:

1. ✅ DJ solicitud procesada
2. ✅ Agente compiló playlist ({len(final_json['tracks'])} tracks, {final_json['duration']:.1f} min)
3. ✅ Propuesta guardada con token (ID: {proposal_id})
4. ✅ PM aprobó vía HTTP
5. ✅ Finalize generó JSON validado

LISTO PARA:
- Transmitir en radio
- Publicar en plataforma
- Compartir con DJ
- Guardar en historial

Status final: "finalized" (ready for broadcast)
""")
print("=" * 80)

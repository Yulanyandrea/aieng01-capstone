#!/usr/bin/env python3
"""Test request_03: Multi-fase (Golden Set)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentes.dj_agent import DJPlaylistAgent
from proposal_storage import ProposalStorage
import json

print("=" * 70)
print("TEST: request_03 - Multi-fase (GOLDEN SET)")
print("=" * 70)

ProposalStorage.clear_all()

agent = DJPlaylistAgent()
agent.dj_email = "alex@dj.local"
agent.user_id = "alex"

request = """DJ: Alex
Duración: 90 minutos (sets de 45 + 45)
Fase 1: 110 BPM a 120 BPM, tonos menores
Fase 2: 120 BPM a 130 BPM, tonos mayores
Transiciones suaves solo entre pistas armónicas
Sin artistas repetidos en ambas fases
Público: After Hours (vibe oscuro)"""

print(f"\n🎤 Request:\n{request}\n")

agent.run(request)

# Verificar propuesta guardada
proposals = ProposalStorage.list_proposals_by_dj("alex@dj.local")
print(f"\n📊 Propuestas generadas: {len(proposals)}")

if proposals:
    prop = proposals[0]
    print(f"  Proposal ID: {prop['proposal_id']}")
    print(f"  Status: {prop['status']}")

    # Simular aprobación
    print("\n✅ Aprobando propuesta (simulado)...")
    # En prod, PM clickearia checkpoint_url, pero aquí lo hacemos manual
    if prop.get("phase_1_tracks") and prop.get("phase_2_tracks"):
        print(f"\n  ✅ Fase 1: {len(prop['phase_1_tracks'])} tracks")
        print(f"  ✅ Fase 2: {len(prop['phase_2_tracks'])} tracks")

print("\n" + "=" * 70)
print("✅ TEST COMPLETADO")
print("=" * 70)

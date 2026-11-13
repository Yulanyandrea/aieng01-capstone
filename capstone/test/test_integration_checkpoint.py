#!/usr/bin/env python3
"""Test integración: agente genera playlist → checkpoint"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentes.dj_agent import DJPlaylistAgent
from proposal_storage import ProposalStorage

print("=" * 70)
print("TEST: Integración DJ Agent + Checkpoint")
print("=" * 70)

# Limpia proposals
ProposalStorage.clear_all()

# Crea agente
agent = DJPlaylistAgent()
agent.dj_email = "test_dj@local"  # Override email

# Test 1: Request simple
print("\n🎤 Test 1: Request simple (45 min)")
request_1 = """DJ: TestDJ
Duración: 45 minutos
BPM: 115 a 128
Tonos: Do Mayor familia
Restricción: Sin repetir artistas
Género: House/Tech House"""

agent.run(request_1)

# Verifica propuesta generada
proposals = ProposalStorage.list_proposals_by_dj("test_dj@local")
print(f"\n📊 Propuestas generadas: {len(proposals)}")
if proposals:
    for prop in proposals:
        print(f"  - {prop['proposal_id']}: {prop['status']}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETADO")
print("=" * 70)

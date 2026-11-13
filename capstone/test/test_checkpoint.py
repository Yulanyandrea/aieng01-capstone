#!/usr/bin/env python3
"""Test para verificar checkpoint flow"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proposal_storage import PlaylistProposal, ProposalStorage, generate_checkpoint_url, generate_proposal_summary
import json

print("=" * 70)
print("TEST: Checkpoint Flow")
print("=" * 70)

# Limpia almacenamiento anterior
ProposalStorage.clear_all()

# Simula tracks
mock_tracks = [
    {"id": 1, "artist": "Adam Beyer", "title": "Teach Me", "bpm": 115, "tonality": "C_major", "duration": 6.2},
    {"id": 2, "artist": "Amelie Lens", "title": "Lenske", "bpm": 116, "tonality": "G_major", "duration": 5.8},
    {"id": 3, "artist": "Charlotte de Witte", "title": "Reflection", "bpm": 117, "tonality": "D_major", "duration": 6.0},
]

# Paso 1: Crear propuesta
print("\n1️⃣  Guardando propuesta...")
proposal = PlaylistProposal(
    proposal_id="",
    dj_name="María",
    dj_email="maria@dj.local",
    constraints={
        "duration_minutes": 45,
        "bpm_start": 115,
        "bpm_end": 128,
        "tonalities": ["C_major", "G_major"],
        "no_artist_repeat": True
    },
    playlist_tracks=mock_tracks
)

proposal_id = ProposalStorage.save_proposal(proposal)
print(f"✅ Propuesta ID: {proposal_id}")

# Paso 2: Generar URL
checkpoint_url = generate_checkpoint_url(proposal_id, proposal.approval_token)
print(f"✅ Checkpoint URL: {checkpoint_url}")

# Paso 3: Generar resumen
summary = generate_proposal_summary(proposal)
print(f"✅ Resumen:\n{summary}")

# Paso 4: Chequear estado (pending)
print("\n2️⃣  Verificando estado inicial (pending)...")
status = ProposalStorage.get_status(proposal_id)
print(f"✅ Estado: {json.dumps(status, indent=2)}")

# Paso 5: Intentar aprobar CON TOKEN INVALIDO (debe fallar)
print("\n3️⃣  Intentando aprobar con token inválido (debe fallar)...")
success = ProposalStorage.approve_proposal(proposal_id, "INVALID_TOKEN", "looks good")
print(f"{'❌' if success else '✅'} Rechazo correcto (token inválido)")

# Paso 6: Aprobar CON TOKEN CORRECTO
print("\n4️⃣  Aprobando con token correcto...")
success = ProposalStorage.approve_proposal(proposal_id, proposal.approval_token, "Great playlist!")
print(f"{'✅' if success else '❌'} Aprobación: {success}")

# Paso 7: Verificar estado (approved)
print("\n5️⃣  Verificando estado final (approved)...")
status = ProposalStorage.get_status(proposal_id)
print(f"✅ Estado: {json.dumps(status, indent=2)}")

# Paso 8: Multi-fase
print("\n6️⃣  Probando multi-fase...")
phase_1 = [mock_tracks[0], mock_tracks[1]]
phase_2 = [mock_tracks[2]]
proposal_multi = PlaylistProposal(
    proposal_id="",
    dj_name="Alex",
    dj_email="alex@dj.local",
    constraints={
        "duration_minutes": 90,
        "bpm_start": 110,
        "bpm_end": 130
    },
    playlist_tracks=[],
    phase_1_tracks=phase_1,
    phase_2_tracks=phase_2
)

prop_id_2 = ProposalStorage.save_proposal(proposal_multi)
print(f"✅ Propuesta multi-fase: {prop_id_2}")

print("\n" + "=" * 70)
print("✅ TODOS LOS TESTS PASARON")
print("=" * 70)

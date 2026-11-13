#!/usr/bin/env python3
"""Test finalize endpoint"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proposal_storage import PlaylistProposal, ProposalStorage
from checkpoint_server import app
import json

print("=" * 70)
print("TEST: Finalize Endpoint")
print("=" * 70)

# Setup
ProposalStorage.clear_all()
app.config['TESTING'] = True
client = app.test_client()

# Mock tracks
mock_tracks = [
    {"id": 1, "artist": "Adam Beyer", "title": "Teach Me", "bpm": 115, "tonality": "C_major", "duration": 6.2},
    {"id": 2, "artist": "Amelie Lens", "title": "Lenske", "bpm": 116, "tonality": "G_major", "duration": 5.8},
    {"id": 3, "artist": "Charlotte de Witte", "title": "Reflection", "bpm": 117, "tonality": "D_major", "duration": 6.0},
]

# ============================================================================
# TEST 1: Finalize pending proposal (debe fallar)
# ============================================================================
print("\n1️⃣  Test: Finalize pending proposal (debe fallar)")
proposal = PlaylistProposal(
    proposal_id="",
    dj_name="María",
    dj_email="maria@dj.local",
    constraints={"duration_minutes": 45},
    playlist_tracks=mock_tracks
)
prop_id = ProposalStorage.save_proposal(proposal)
print(f"   Creada propuesta: {prop_id} (status: pending)")

response = client.post(f'/finalize/{prop_id}')
print(f"   Response: {response.status_code}")
if response.status_code == 400:
    print("   ✅ Correcto: rechaza pending")
else:
    print(f"   ❌ Error: esperaba 400, got {response.status_code}")

# ============================================================================
# TEST 2: Finalize approved proposal (debe funcionar)
# ============================================================================
print("\n2️⃣  Test: Finalize approved proposal")

# Aprobar propuesta
approval_success = ProposalStorage.approve_proposal(
    prop_id,
    proposal.approval_token,
    "Great mix!"
)
print(f"   Propuesta aprobada: {approval_success}")

response = client.post(f'/finalize/{prop_id}')
print(f"   Response: {response.status_code}")

if response.status_code == 200:
    data = response.get_json()
    print(f"   ✅ Status: {data.get('status')}")
    print(f"   ✅ Tracks: {len(data.get('tracks', []))} tracks")
    print(f"   ✅ Duration: {data.get('duration', 0):.1f} min")
    print(f"   ✅ BPM range: {data.get('bpm_range')}")
    print(f"   ✅ Feedback: {data.get('feedback')}")
else:
    data = response.get_json()
    print(f"   ❌ Error: {data.get('error')}")

# ============================================================================
# TEST 3: Multi-fase finalize
# ============================================================================
print("\n3️⃣  Test: Multi-fase finalize")

phase_1 = mock_tracks[:2]
phase_2 = mock_tracks[1:]

proposal_multi = PlaylistProposal(
    proposal_id="",
    dj_name="Alex",
    dj_email="alex@dj.local",
    constraints={"duration_minutes": 90},
    playlist_tracks=[],  # Empty for multi-phase
    phase_1_tracks=phase_1,
    phase_2_tracks=phase_2
)

prop_id_2 = ProposalStorage.save_proposal(proposal_multi)
ProposalStorage.approve_proposal(prop_id_2, proposal_multi.approval_token, "Perfect!")

response = client.post(f'/finalize/{prop_id_2}')
if response.status_code == 200:
    data = response.get_json()
    print(f"   ✅ Phase 1: {len(data.get('phase_1', {}).get('tracks', []))} tracks, {data.get('phase_1', {}).get('duration', 0):.1f} min")
    print(f"   ✅ Phase 2: {len(data.get('phase_2', {}).get('tracks', []))} tracks, {data.get('phase_2', {}).get('duration', 0):.1f} min")
else:
    print(f"   ❌ Error: {response.get_json()}")

# ============================================================================
# TEST 4: Non-existent proposal
# ============================================================================
print("\n4️⃣  Test: Non-existent proposal")
response = client.post('/finalize/nonexistent')
if response.status_code == 404:
    print("   ✅ Correcto: retorna 404")
else:
    print(f"   ❌ Error: esperaba 404, got {response.status_code}")

# ============================================================================
# PRETTY PRINT
# ============================================================================
print("\n5️⃣  Pretty-print final JSON output:")
response = client.post(f'/finalize/{prop_id}')
if response.status_code == 200:
    data = response.get_json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")

print("\n" + "=" * 70)
print("✅ TODOS LOS TESTS COMPLETADOS")
print("=" * 70)

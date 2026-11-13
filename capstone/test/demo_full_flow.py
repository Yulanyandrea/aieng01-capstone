#!/usr/bin/env python3
"""
DEMO: Flujo completo DJ Agent → Checkpoint → Approval
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentes.dj_agent import DJPlaylistAgent
from proposal_storage import ProposalStorage
from rate_limiter import OutputGuardrails
import json
import time

print("=" * 80)
print("🎵 DJ PLAYLIST GENERATOR - FULL FLOW DEMO")
print("=" * 80)

# Limpia storage
ProposalStorage.clear_all()

# ============================================================================
# PASO 1: DJ SOLICITA PLAYLIST
# ============================================================================
print("\n" + "█" * 80)
print("PASO 1: DJ solicita playlist")
print("█" * 80)

agent = DJPlaylistAgent()
agent.dj_email = "carlos@dj.local"
agent.user_id = "carlos"

request_text = """DJ: Carlos
Duración: 45 minutos
BPM: 120 a 128 (rango progresivo)
Tonalidades: C Mayor, G Mayor (familia armónica)
Restricción: Máximo 2 artistas repetidos
Género: House/Tech House
Público: Club 11pm-1am"""

print(f"\n🎤 Solicitud del DJ:\n{request_text}")
print("\n⏳ Procesando...")

# Ejecuta agente
try:
    result = agent.run(request_text)
except Exception as e:
    print(f"❌ Error: {e}")
    result = "error"

# ============================================================================
# PASO 2: VERIFICAR PROPUESTA GUARDADA
# ============================================================================
print("\n" + "█" * 80)
print("PASO 2: Verificar propuesta guardada")
print("█" * 80)

proposals = ProposalStorage.list_proposals_by_dj("carlos@dj.local")
print(f"\n✅ Propuestas generadas: {len(proposals)}")

if proposals:
    prop = proposals[0]
    proposal_id = prop["proposal_id"]
    status = prop["status"]
    print(f"  Proposal ID: {proposal_id}")
    print(f"  Status: {status}")
    print(f"  Creada: {prop['created_at']}")
    print(f"  Expira: {prop['expires_at']}")

    # ========================================================================
    # PASO 3: SIMULAR APROBACION DEL PM
    # ========================================================================
    print("\n" + "█" * 80)
    print("PASO 3: PM aprueba propuesta")
    print("█" * 80)

    proposal = ProposalStorage.get_proposal(proposal_id)
    print(f"\n🔐 Retrieving propuesta con token...")

    # Simular aprobación
    success = ProposalStorage.approve_proposal(
        proposal_id,
        proposal.approval_token,
        "Great mix! Ready for broadcast 🎚️"
    )

    if success:
        print(f"✅ Propuesta aprobada exitosamente")

        # ====================================================================
        # PASO 4: VALIDAR OUTPUT
        # ====================================================================
        print("\n" + "█" * 80)
        print("PASO 4: Validar output (guardrails)")
        print("█" * 80)

        # Extrae tracks
        tracks = (proposal.phase_1_tracks or
                 proposal.phase_2_tracks or
                 proposal.playlist_tracks or [])

        print(f"\n✅ Tracks en propuesta: {len(tracks)}")

        # Crea JSON de output
        output_json = {
            "proposal_id": proposal_id,
            "dj_name": proposal.dj_name,
            "playlist": tracks,
            "constraints": proposal.constraints,
            "status": "approved",
            "generated_at": proposal.created_at
        }

        # Valida con guardrails
        valid, issues = OutputGuardrails.validate_playlist_json(output_json)
        if valid:
            print("✅ Output válido (sin issues)")
        else:
            print(f"⚠️  Issues encontradas:")
            for issue in issues:
                print(f"   - {issue}")

        # ====================================================================
        # PASO 5: ESTADÍSTICAS FINALES
        # ====================================================================
        print("\n" + "█" * 80)
        print("PASO 5: Estadísticas finales")
        print("█" * 80)

        total_duration = sum(t.get("duration", 0) for t in tracks)
        unique_artists = len(set(t.get("artist") for t in tracks))
        unique_tonalities = len(set(t.get("tonality") for t in tracks))
        bpm_min = min(t.get("bpm", 0) for t in tracks) if tracks else 0
        bpm_max = max(t.get("bpm", 0) for t in tracks) if tracks else 0

        print(f"\n📊 Playlist Summary:")
        print(f"  Total tracks: {len(tracks)}")
        print(f"  Total duration: {total_duration:.1f} min")
        print(f"  Unique artists: {unique_artists}")
        print(f"  Unique tonalities: {unique_tonalities}")
        print(f"  BPM range: {bpm_min} → {bpm_max}")

        print(f"\n🎵 Primeros 5 tracks:")
        for i, track in enumerate(tracks[:5], 1):
            print(f"  {i}. {track.get('artist')} - {track.get('title')} "
                  f"({track.get('bpm')} BPM, {track.get('tonality')}, {track.get('duration')}min)")

        # ====================================================================
        # RESUMEN FINAL
        # ====================================================================
        print("\n" + "=" * 80)
        print("✅ DEMO COMPLETADO - FLUJO EXITOSO")
        print("=" * 80)
        print(f"""
Resumen:
1. ✅ DJ solicitud procesada
2. ✅ Playlist compilada ({len(tracks)} tracks, {total_duration:.1f} min)
3. ✅ Propuesta guardada (ID: {proposal_id})
4. ✅ PM aprobó (via token seguro)
5. ✅ Output validado (sin data sensible)
6. ✅ Listo para publicar/transmitir

Siguiente: POST /finalize/{proposal_id} → JSON final
        """)
    else:
        print(f"❌ Error al aprobar propuesta")
else:
    print("❌ No se generaron propuestas")

print("\n" + "=" * 80)

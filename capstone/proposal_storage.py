"""
Proposal Storage + Checkpoint Management
Maneja guardado de propuestas, generación de URLs, y seguimiento de aprobaciones.
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PlaylistProposal:
    """Una propuesta de playlist pendiente de aprobación"""
    proposal_id: str
    dj_name: str
    dj_email: str  # no se expone en JSON final
    constraints: Dict
    playlist_tracks: List[Dict]  # [{"id": int, "artist": str, ...}, ...]
    phase_1_tracks: Optional[List[Dict]] = None  # Para multi-fase
    phase_2_tracks: Optional[List[Dict]] = None
    status: str = "pending_approval"  # pending_approval | approved | rejected
    created_at: str = ""
    approved_at: Optional[str] = None
    expires_at: str = ""
    approval_token: str = ""  # Token único para validar aprobador
    feedback: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.expires_at:
            # Expira en 24 horas
            expire_time = datetime.utcnow() + timedelta(hours=24)
            self.expires_at = expire_time.isoformat()
        if not self.approval_token:
            # Token único para PM original
            self.approval_token = secrets.token_urlsafe(32)

    def is_expired(self) -> bool:
        """Chequea si la propuesta ya expiró"""
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > expires

    def to_dict(self) -> Dict:
        """Convierte a dict (incluyendo datos sensibles)"""
        return asdict(self)

    def to_public_dict(self) -> Dict:
        """Retorna dict SIN datos sensibles (dj_email, approval_token)"""
        d = asdict(self)
        d.pop("dj_email", None)
        d.pop("approval_token", None)
        return d


# ============================================================================
# IN-MEMORY STORAGE (MVP)
# Reemplazar con BD real en prod
# ============================================================================

class ProposalStorage:
    """Almacena propuestas en memoria (MVP). En prod → PostgreSQL/MongoDB"""

    _proposals: Dict[str, PlaylistProposal] = {}
    _proposal_counter = 0

    @classmethod
    def save_proposal(cls, proposal: PlaylistProposal) -> str:
        """Guarda propuesta, retorna proposal_id"""
        if not proposal.proposal_id:
            cls._proposal_counter += 1
            proposal.proposal_id = f"prop_{cls._proposal_counter:05d}"

        # Validaciones
        if proposal.proposal_id in cls._proposals:
            raise ValueError(f"Proposal {proposal.proposal_id} ya existe (NO idempotente)")
        if not proposal.playlist_tracks and not (proposal.phase_1_tracks or proposal.phase_2_tracks):
            raise ValueError("Propuesta vacía: sin tracks")

        cls._proposals[proposal.proposal_id] = proposal
        print(f"💾 Propuesta guardada: {proposal.proposal_id}")
        return proposal.proposal_id

    @classmethod
    def get_proposal(cls, proposal_id: str) -> Optional[PlaylistProposal]:
        """Lee propuesta por ID"""
        proposal = cls._proposals.get(proposal_id)
        if proposal and proposal.is_expired():
            # Propuesta expirada
            return None
        return proposal

    @classmethod
    def approve_proposal(cls, proposal_id: str, token: str, feedback: str = "") -> bool:
        """
        Aprueba propuesta si token es válido.
        Retorna True si aprobada, False si token inválido/propuesta no existe.
        """
        proposal = cls._proposals.get(proposal_id)
        if not proposal:
            return False
        if proposal.approval_token != token:
            return False
        if proposal.is_expired():
            return False

        proposal.status = "approved"
        proposal.approved_at = datetime.utcnow().isoformat()
        proposal.feedback = feedback
        return True

    @classmethod
    def reject_proposal(cls, proposal_id: str, token: str, feedback: str = "") -> bool:
        """Rechaza propuesta si token es válido"""
        proposal = cls._proposals.get(proposal_id)
        if not proposal:
            return False
        if proposal.approval_token != token:
            return False

        proposal.status = "rejected"
        proposal.feedback = feedback
        return True

    @classmethod
    def get_status(cls, proposal_id: str) -> Dict:
        """Retorna estado de propuesta (público)"""
        proposal = cls._proposals.get(proposal_id)
        if not proposal:
            return {"error": "Proposal not found"}
        if proposal.is_expired():
            return {"error": "Proposal expired"}

        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "created_at": proposal.created_at,
            "expires_at": proposal.expires_at,
            "approved_at": proposal.approved_at,
            "feedback": proposal.feedback
        }

    @classmethod
    def list_proposals_by_dj(cls, dj_email: str) -> List[Dict]:
        """Lista propuestas de un DJ específico"""
        return [
            p.to_public_dict()
            for p in cls._proposals.values()
            if p.dj_email == dj_email and not p.is_expired()
        ]

    @classmethod
    def clear_all(cls):
        """Limpia almacenamiento (para tests)"""
        cls._proposals.clear()
        cls._proposal_counter = 0


# ============================================================================
# CHECKPOINT URL GENERATION
# ============================================================================

def generate_checkpoint_url(proposal_id: str, token: str, base_url: str = "http://localhost:8000") -> str:
    """Genera URL para que PM apruebe/rechace"""
    return f"{base_url}/checkpoint/{proposal_id}?token={token}"


def generate_proposal_summary(proposal: PlaylistProposal) -> str:
    """Genera resumen legible para PM"""
    summary = f"""
PROPUESTA DE PLAYLIST - {proposal.proposal_id}
{'=' * 60}

DJ: {proposal.dj_name}
Creada: {proposal.created_at}
Expira: {proposal.expires_at}

RESTRICCIONES:
- Duración: {proposal.constraints.get('duration_minutes')} min
- BPM: {proposal.constraints.get('bpm_start')} → {proposal.constraints.get('bpm_end')}
- Tonalidades: {', '.join(proposal.constraints.get('tonalities', []))}
- Sin artistas repetidos: {proposal.constraints.get('no_artist_repeat')}

TRACKS GENERADOS:
"""
    if proposal.phase_1_tracks:
        summary += f"\n--- FASE 1 ({len(proposal.phase_1_tracks)} tracks) ---\n"
        for i, track in enumerate(proposal.phase_1_tracks, 1):
            duration = track.get('duration', 0)
            summary += f"{i}. {track.get('artist')} - {track.get('title')} ({track.get('bpm')} BPM, {track.get('tonality')}, {duration}min)\n"

    if proposal.phase_2_tracks:
        summary += f"\n--- FASE 2 ({len(proposal.phase_2_tracks)} tracks) ---\n"
        for i, track in enumerate(proposal.phase_2_tracks, 1):
            duration = track.get('duration', 0)
            summary += f"{i}. {track.get('artist')} - {track.get('title')} ({track.get('bpm')} BPM, {track.get('tonality')}, {duration}min)\n"

    if proposal.playlist_tracks:
        summary += f"\n--- PLAYLIST ({len(proposal.playlist_tracks)} tracks) ---\n"
        for i, track in enumerate(proposal.playlist_tracks, 1):
            duration = track.get('duration', 0)
            summary += f"{i}. {track.get('artist')} - {track.get('title')} ({track.get('bpm')} BPM, {track.get('tonality')}, {duration}min)\n"

    summary += f"""
{'=' * 60}
🔗 CHECKPOINT: {generate_checkpoint_url(proposal.proposal_id, proposal.approval_token)}
"""
    return summary

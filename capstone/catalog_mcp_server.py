"""
Catalog MCP Server
Expone el catálogo de tracks como servidor MCP con herramientas:
- search_tracks(bpm_range, tonalities, exclude_artists, exclude_ids)
- get_track_metadata(track_id)
- validate_catalog_feasibility(constraints)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# MOCK CATALOG
# ============================================================================

MOCK_TRACKS = [
    {"id": 1, "artist": "Adam Beyer", "title": "Teach Me", "bpm": 115, "tonality": "C_major", "duration": 6.2, "genre": "Tech House"},
    {"id": 2, "artist": "Amelie Lens", "title": "Lenske", "bpm": 116, "tonality": "G_major", "duration": 5.8, "genre": "Tech House"},
    {"id": 3, "artist": "Charlotte de Witte", "title": "Reflection", "bpm": 117, "tonality": "D_major", "duration": 6.0, "genre": "Techno"},
    {"id": 4, "artist": "Richie Hawtin", "title": "Spastik", "bpm": 118, "tonality": "A_major", "duration": 5.9, "genre": "Tech House"},
    {"id": 5, "artist": "Adam Beyer", "title": "Your Mind", "bpm": 120, "tonality": "E_major", "duration": 6.1, "genre": "Techno"},
    {"id": 6, "artist": "Amelie Lens", "title": "Contradict", "bpm": 121, "tonality": "B_major", "duration": 5.7, "genre": "Tech House"},
    {"id": 7, "artist": "Carl Cox", "title": "Plink Plonk", "bpm": 122, "tonality": "F#_major", "duration": 6.3, "genre": "Techno"},
    {"id": 8, "artist": "Laurent Garnier", "title": "Crispy Bacon", "bpm": 123, "tonality": "C#_major", "duration": 5.9, "genre": "House"},
    {"id": 9, "artist": "Charlotte de Witte", "title": "Control", "bpm": 124, "tonality": "G#_major", "duration": 6.2, "genre": "Techno"},
    {"id": 10, "artist": "Richie Hawtin", "title": "DE9", "bpm": 125, "tonality": "D#_major", "duration": 6.0, "genre": "Tech House"},
    {"id": 11, "artist": "Nina Kraviz", "title": "Ghosts", "bpm": 126, "tonality": "A#_major", "duration": 5.8, "genre": "Techno"},
    {"id": 12, "artist": "Adam Beyer", "title": "Rave", "bpm": 127, "tonality": "C_major", "duration": 6.1, "genre": "Techno"},
    {"id": 13, "artist": "Amelie Lens", "title": "Breach", "bpm": 128, "tonality": "G_major", "duration": 5.9, "genre": "Tech House"},
    {"id": 14, "artist": "Charlotte de Witte", "title": "Veiled", "bpm": 129, "tonality": "D_major", "duration": 6.2, "genre": "Techno"},
    {"id": 15, "artist": "Richie Hawtin", "title": "Minus", "bpm": 130, "tonality": "A_major", "duration": 6.0, "genre": "Tech House"},
]

# Ampliamos a ~100 tracks
for i in range(16, 101):
    artist_pool = ["Adam Beyer", "Amelie Lens", "Charlotte de Witte", "Richie Hawtin", "Nina Kraviz", "Carl Cox", "Laurent Garnier", "Jeff Mills", "Chris Liebing", "Oliver Huntemann"]
    tonality_pool = ["C_major", "G_major", "D_major", "A_major", "E_major", "B_major", "F#_major", "C#_major", "A_minor", "E_minor"]

    MOCK_TRACKS.append({
        "id": i,
        "artist": artist_pool[i % len(artist_pool)],
        "title": f"Track {i}",
        "bpm": 110 + (i % 25),
        "tonality": tonality_pool[i % len(tonality_pool)],
        "duration": 5.5 + (i % 10) * 0.1,
        "genre": ["House", "Tech House", "Techno"][i % 3]
    })

# ============================================================================
# CATALOG SERVICE (MCP Backend)
# ============================================================================

class CatalogService:
    """Servicio de catálogo expuesto via MCP"""

    @staticmethod
    def search_tracks(
        bpm_min: int,
        bpm_max: int,
        tonalities: List[str],
        exclude_artists: Optional[List[str]] = None,
        exclude_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Busca tracks que cumplan criterios.
        Retorna lista ordenada por BPM.
        """
        exclude_artists = exclude_artists or []
        exclude_ids = exclude_ids or []

        results = [
            t for t in MOCK_TRACKS
            if (bpm_min <= t["bpm"] <= bpm_max and
                t["tonality"] in tonalities and
                t["artist"] not in exclude_artists and
                t["id"] not in exclude_ids)
        ]

        results.sort(key=lambda x: x["bpm"])
        return results

    @staticmethod
    def get_track_metadata(track_id: int) -> Optional[Dict]:
        """Obtiene metadatos de un track por ID"""
        for track in MOCK_TRACKS:
            if track["id"] == track_id:
                return track
        return None

    @staticmethod
    def validate_catalog_feasibility(
        bpm_start: int,
        bpm_end: int,
        tonalities: List[str],
        duration_minutes: int,
        no_artist_repeat: bool = False
    ) -> Tuple[bool, str]:
        """
        Valida si el catálogo puede cumplir las restricciones.
        Retorna: (es_viable, mensaje_explicativo)
        """
        # Check BPM coverage
        tracks_in_range = [t for t in MOCK_TRACKS if bpm_start <= t["bpm"] <= bpm_end]
        if not tracks_in_range:
            return False, f"❌ No hay tracks en rango BPM {bpm_start}-{bpm_end}"

        # Check tonalities
        tracks_with_tonality = [t for t in tracks_in_range if t["tonality"] in tonalities]
        if not tracks_with_tonality:
            return False, f"❌ No hay tracks en tonalidades {tonalities}"

        # Check duration (rough: 5.5-6 min per track)
        min_tracks_needed = int(duration_minutes / 6) + 1
        available_unique_artists = len(set(t["artist"] for t in tracks_with_tonality))

        if no_artist_repeat and min_tracks_needed > available_unique_artists:
            return False, f"⚠️ Necesitas {min_tracks_needed} tracks sin repetir artistas, pero solo hay {available_unique_artists} artistas disponibles"

        if min_tracks_needed > len(tracks_with_tonality):
            return False, f"⚠️ Necesitas ~{min_tracks_needed} tracks pero solo hay {len(tracks_with_tonality)} disponibles"

        # Viability score
        artists_available = available_unique_artists if no_artist_repeat else "unlimited"
        return True, f"✅ Viable: {len(tracks_with_tonality)} tracks disponibles, {artists_available} artistas"

    @staticmethod
    def get_catalog_stats() -> Dict:
        """Retorna estadísticas del catálogo"""
        return {
            "total_tracks": len(MOCK_TRACKS),
            "unique_artists": len(set(t["artist"] for t in MOCK_TRACKS)),
            "bpm_range": (
                min(t["bpm"] for t in MOCK_TRACKS),
                max(t["bpm"] for t in MOCK_TRACKS)
            ),
            "tonalities": sorted(list(set(t["tonality"] for t in MOCK_TRACKS))),
            "genres": sorted(list(set(t["genre"] for t in MOCK_TRACKS)))
        }

# ============================================================================
# MCP TOOL DEFINITIONS (para ser consumidas por Claude)
# ============================================================================

def get_mcp_tools() -> List[Dict]:
    """Retorna definiciones de herramientas MCP para Claude"""
    return [
        {
            "name": "search_tracks",
            "description": "Busca tracks en el catálogo según criterios (BPM, tonalidad, artistas excluidos)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "bpm_min": {"type": "integer", "description": "BPM mínimo"},
                    "bpm_max": {"type": "integer", "description": "BPM máximo"},
                    "tonalities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tonalidades permitidas (ej: ['C_major', 'G_major'])"
                    },
                    "exclude_artists": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Artistas a excluir (opcional)"
                    },
                    "exclude_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "IDs de tracks a excluir (opcional)"
                    }
                },
                "required": ["bpm_min", "bpm_max", "tonalities"]
            }
        },
        {
            "name": "get_track_metadata",
            "description": "Obtiene metadatos detallados de un track específico",
            "input_schema": {
                "type": "object",
                "properties": {
                    "track_id": {"type": "integer", "description": "ID del track"}
                },
                "required": ["track_id"]
            }
        },
        {
            "name": "validate_catalog_feasibility",
            "description": "Valida si el catálogo puede cumplir con las restricciones especificadas",
            "input_schema": {
                "type": "object",
                "properties": {
                    "bpm_start": {"type": "integer"},
                    "bpm_end": {"type": "integer"},
                    "tonalities": {"type": "array", "items": {"type": "string"}},
                    "duration_minutes": {"type": "integer"},
                    "no_artist_repeat": {"type": "boolean"}
                },
                "required": ["bpm_start", "bpm_end", "tonalities", "duration_minutes"]
            }
        },
        {
            "name": "get_catalog_stats",
            "description": "Retorna estadísticas generales del catálogo disponible",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "save_playlist_proposal",
            "description": "Guarda propuesta de playlist para checkpoint humano (aprobación del PM). Retorna proposal_id + checkpoint_url",
            "input_schema": {
                "type": "object",
                "properties": {
                    "dj_name": {"type": "string"},
                    "dj_email": {"type": "string"},
                    "constraints": {
                        "type": "object",
                        "description": "Restricciones originales"
                    },
                    "playlist_tracks": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Tracks en single-phase, o vacío si multi-fase"
                    },
                    "phase_1_tracks": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Tracks fase 1 (opcional)"
                    },
                    "phase_2_tracks": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Tracks fase 2 (opcional)"
                    }
                },
                "required": ["dj_name", "dj_email", "constraints"]
            }
        },
        {
            "name": "get_proposal_status",
            "description": "Obtiene estado de propuesta (pending/approved/rejected). Retorna null si no existe o expiró.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "string"}
                },
                "required": ["proposal_id"]
            }
        }
    ]

def process_mcp_tool_call(tool_name: str, tool_input: Dict) -> str:
    """Procesa llamadas MCP y retorna resultados como JSON string"""
    try:
        if tool_name == "search_tracks":
            results = CatalogService.search_tracks(
                bpm_min=tool_input.get("bpm_min"),
                bpm_max=tool_input.get("bpm_max"),
                tonalities=tool_input.get("tonalities", []),
                exclude_artists=tool_input.get("exclude_artists"),
                exclude_ids=tool_input.get("exclude_ids")
            )
            return json.dumps(results)

        elif tool_name == "get_track_metadata":
            result = CatalogService.get_track_metadata(tool_input.get("track_id"))
            return json.dumps(result) if result else json.dumps({"error": "Track not found"})

        elif tool_name == "validate_catalog_feasibility":
            is_viable, message = CatalogService.validate_catalog_feasibility(
                bpm_start=tool_input.get("bpm_start"),
                bpm_end=tool_input.get("bpm_end"),
                tonalities=tool_input.get("tonalities", []),
                duration_minutes=tool_input.get("duration_minutes"),
                no_artist_repeat=tool_input.get("no_artist_repeat", False)
            )
            return json.dumps({"viable": is_viable, "message": message})

        elif tool_name == "get_catalog_stats":
            stats = CatalogService.get_catalog_stats()
            return json.dumps(stats)

        elif tool_name == "save_playlist_proposal":
            # Import here to avoid circular dependency
            from proposal_storage import PlaylistProposal, ProposalStorage, generate_checkpoint_url, generate_proposal_summary

            try:
                proposal = PlaylistProposal(
                    proposal_id="",  # Auto-generated
                    dj_name=tool_input.get("dj_name", "DJ"),
                    dj_email=tool_input.get("dj_email", "unknown@dj.local"),
                    constraints=tool_input.get("constraints", {}),
                    playlist_tracks=tool_input.get("playlist_tracks", []),
                    phase_1_tracks=tool_input.get("phase_1_tracks"),
                    phase_2_tracks=tool_input.get("phase_2_tracks")
                )
                proposal_id = ProposalStorage.save_proposal(proposal)
                checkpoint_url = generate_checkpoint_url(proposal_id, proposal.approval_token)
                summary = generate_proposal_summary(proposal)

                return json.dumps({
                    "success": True,
                    "proposal_id": proposal_id,
                    "checkpoint_url": checkpoint_url,
                    "expires_at": proposal.expires_at,
                    "summary": summary
                })
            except ValueError as e:
                return json.dumps({"error": str(e)})

        elif tool_name == "get_proposal_status":
            from proposal_storage import ProposalStorage

            proposal_id = tool_input.get("proposal_id")
            status = ProposalStorage.get_status(proposal_id)
            return json.dumps(status)

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})

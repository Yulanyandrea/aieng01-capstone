"""
DJ Playlist Generator Agent (Refactored with MCP + Subagent)
- Usa MCP Catalog Service para búsquedas
- Invoca Constraint Validator subagent para restricciones complejas
- Mantiene lógica de generación de playlist
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from anthropic import Anthropic

# Add parent directory to path for sibling imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog_mcp_server import get_mcp_tools, process_mcp_tool_call, CatalogService
from agentes.constraint_validator_agent import ConstraintValidatorAgent
from rate_limiter import RateLimiter, OutputGuardrails

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ParsedConstraints:
    """Restricciones normalizadas de una solicitud DJ"""
    dj_name: str = "DJ"
    duration_minutes: int = 45
    bpm_start: int = 115
    bpm_end: int = 128
    tonalities: List[str] = None
    no_artist_repeat: bool = False
    max_artist_repeats: int = 999
    genre: Optional[str] = None
    phases: Optional[List[Dict]] = None

    def __post_init__(self):
        if self.tonalities is None:
            self.tonalities = ["C_major"]


@dataclass
class GeneratedPlaylist:
    """Resultado de compilation"""
    phase_1_tracks: Optional[List[Dict]] = None
    phase_2_tracks: Optional[List[Dict]] = None
    playlist_tracks: Optional[List[Dict]] = None  # single-phase

# ============================================================================
# PARSING & LOGIC (LOCAL)
# ============================================================================

def parse_dj_request(request_text: str) -> ParsedConstraints:
    """Parse unstructured DJ request → normalized Constraints"""
    lines = request_text.lower()

    # Extract duration
    duration_match = re.search(r'(\d+)\s*(?:minuto|min|m)', lines)
    duration = int(duration_match.group(1)) if duration_match else 45

    # Extract BPM
    bpm_start, bpm_end = 115, 128
    bpm_match = re.search(r'bpm[:\s]+(\d+)\s*[-a]?\s*(\d+)?', lines)
    if bpm_match:
        bpm_start = int(bpm_match.group(1))
        bpm_end = int(bpm_match.group(2)) if bpm_match.group(2) else bpm_start + 10

    # Extract tonalities
    tonalities = ["C_major"]
    if "do mayor" in lines or "c major" in lines:
        tonalities = ["C_major", "G_major", "D_major", "A_major"]

    # Extract restrictions
    no_repeat = "sin repetir artista" in lines or "no repeat" in lines
    max_repeats = 2 if "máximo 2 artistas" in lines else 999

    # Extract genre
    genre = None
    for g in ["house", "tech house", "deep house", "techno"]:
        if g in lines:
            genre = g
            break

    # Check for multi-phase (complex case)
    phases = None
    if "fase" in lines or "phase" in lines:
        phases = [{"phase": 1}, {"phase": 2}]

    return ParsedConstraints(
        dj_name=re.search(r'dj[:\s]+(\w+)', lines).group(1) if re.search(r'dj[:\s]+(\w+)', lines) else "DJ",
        duration_minutes=duration,
        bpm_start=bpm_start,
        bpm_end=bpm_end,
        tonalities=tonalities,
        no_artist_repeat=no_repeat,
        max_artist_repeats=max_repeats,
        genre=genre,
        phases=phases
    )

def are_harmonically_compatible(tone1: str, tone2: str) -> bool:
    """Simple harmonic compatibility check"""
    major_families = {
        "C_major": ["C_major", "G_major", "D_major", "A_major", "A_minor", "E_minor"],
        "G_major": ["G_major", "D_major", "A_major", "E_major", "E_minor", "B_minor"],
        "D_major": ["D_major", "A_major", "E_major", "B_major", "B_minor", "F#_minor"],
        "A_major": ["A_major", "E_major", "B_major", "F#_major", "F#_minor", "C#_minor"],
        "E_major": ["E_major", "B_major", "F#_major", "C#_major"],
    }
    return tone2 in major_families.get(tone1, [tone1])

def build_playlist_greedy(
    constraints: ParsedConstraints,
    candidates_provider
) -> Optional[List[Dict]]:
    """
    Construye playlist con algoritmo greedy.
    Para multi-fase: construye phase_1 independiente, luego phase_2
    candidates_provider: función que retorna candidatos (usa MCP)
    """
    if constraints.phases and len(constraints.phases) >= 2:
        # MULTI-FASE
        return _build_multiphase_playlist(constraints, candidates_provider)
    else:
        # SINGLE-PHASE
        return _build_single_playlist(constraints, candidates_provider)


def _build_single_playlist(constraints: ParsedConstraints, candidates_provider) -> Optional[List[Dict]]:
    """Construye single-phase playlist"""
    playlist = []
    total_duration = 0
    target_duration = constraints.duration_minutes * 60
    exclude_artists = set()
    exclude_ids = set()

    current_bpm = constraints.bpm_start
    current_tone = constraints.tonalities[0]

    while total_duration < target_duration * 0.95:
        search_result = candidates_provider(
            bpm_min=current_bpm,
            bpm_max=constraints.bpm_end,
            tonalities=[t for t in constraints.tonalities if are_harmonically_compatible(current_tone, t)],
            exclude_artists=list(exclude_artists) if constraints.no_artist_repeat else [],
            exclude_ids=list(exclude_ids)
        )

        if not search_result:
            search_result = candidates_provider(
                bpm_min=current_bpm,
                bpm_max=constraints.bpm_end,
                tonalities=constraints.tonalities,
                exclude_ids=list(exclude_ids)
            )

        if not search_result:
            break

        track = search_result[0]
        playlist.append(track)
        total_duration += track["duration"] * 60

        if constraints.no_artist_repeat:
            exclude_artists.add(track["artist"])
        else:
            artist_count = sum(1 for t in playlist if t["artist"] == track["artist"])
            if artist_count >= constraints.max_artist_repeats:
                exclude_artists.add(track["artist"])

        exclude_ids.add(track["id"])
        current_bpm = track["bpm"]
        current_tone = track["tonality"]

        if len(playlist) > 20:
            break

    return playlist if len(playlist) > 0 else None


def _build_multiphase_playlist(constraints: ParsedConstraints, candidates_provider) -> Optional[List[Dict]]:
    """Construye multi-fase playlist (phase_1, phase_2)"""
    duration_per_phase = (constraints.duration_minutes / 2) * 60  # 45 min per phase

    # PHASE 1: Minor tonalities, lower BPM
    phase_1_constraints = ParsedConstraints(
        dj_name=constraints.dj_name,
        duration_minutes=int(constraints.duration_minutes / 2),
        bpm_start=constraints.bpm_start,
        bpm_end=(constraints.bpm_start + constraints.bpm_end) // 2,  # Lower half
        tonalities=[t for t in constraints.tonalities if "minor" in t.lower()] or ["A_minor", "E_minor"],
        no_artist_repeat=constraints.no_artist_repeat,
        max_artist_repeats=constraints.max_artist_repeats,
        genre=constraints.genre
    )

    phase_1 = _build_single_playlist(phase_1_constraints, candidates_provider) or []

    # PHASE 2: Major tonalities, higher BPM, exclude phase_1 artists
    exclude_phase1_artists = set(t["artist"] for t in phase_1)
    phase_2_exclude_artists = list(exclude_phase1_artists) if constraints.no_artist_repeat else []

    # Construct search function wrapper para phase 2
    def phase2_candidates_provider(bpm_min, bpm_max, tonalities, exclude_artists=None, exclude_ids=None):
        exclude_ids = exclude_ids or []
        exclude_ids.extend([t["id"] for t in phase_1])
        actual_exclude_artists = (exclude_artists or []) + phase_2_exclude_artists
        return candidates_provider(bpm_min, bpm_max, tonalities, actual_exclude_artists, exclude_ids)

    phase_2_constraints = ParsedConstraints(
        dj_name=constraints.dj_name,
        duration_minutes=int(constraints.duration_minutes / 2),
        bpm_start=(constraints.bpm_start + constraints.bpm_end) // 2,  # Higher half
        bpm_end=constraints.bpm_end,
        tonalities=[t for t in constraints.tonalities if "major" in t.lower()] or ["C_major", "G_major", "D_major"],
        no_artist_repeat=constraints.no_artist_repeat,
        max_artist_repeats=constraints.max_artist_repeats,
        genre=constraints.genre
    )

    phase_2 = _build_single_playlist(phase_2_constraints, phase2_candidates_provider) or []

    # Retorna ambas fases concatenadas (será dividida luego en checkpoint)
    return phase_1 + phase_2 if (phase_1 or phase_2) else None

def explain_playlist(playlist: List[Dict], constraints: ParsedConstraints) -> str:
    """Genera explicación de por qué cada track está en la playlist"""
    explanation = f"🎵 PLAYLIST PARA {constraints.dj_name.upper()}\n"
    explanation += f"{'=' * 60}\n"
    explanation += f"Duración: {sum(t['duration'] for t in playlist):.1f} min | "
    explanation += f"BPM: {playlist[0]['bpm']} → {playlist[-1]['bpm']} | "
    explanation += f"Tonalidades: {len(set(t['tonality'] for t in playlist))} únicas\n\n"

    for i, track in enumerate(playlist, 1):
        explanation += f"{i:2d}. [{track['bpm']:3d} BPM] {track['artist']:20s} - {track['title']}\n"
        genre = track.get('genre', 'Unknown')
        tonality = track.get('tonality', 'Unknown')
        duration = track.get('duration', 0)
        explanation += f"    Duración: {duration:.1f}min | Tonalidad: {tonality} | Género: {genre}\n"

    total_duration = sum(t['duration'] for t in playlist)
    explanation += f"\n{'=' * 60}\n"
    explanation += f"TOTAL: {total_duration:.1f} minutos ({int(total_duration // 60)}:{int(total_duration % 60):02d})\n"

    return explanation

# ============================================================================
# MAIN AGENT WITH MCP + SUBAGENT
# ============================================================================

class DJPlaylistAgent:
    _rate_limiter = RateLimiter(max_per_session=10, min_interval_seconds=1.0)  # Shared instance

    def __init__(self):
        self.client = Anthropic()
        self.model = "bedrock-claude-sonnet"
        self.conversation_history = []
        self.validator_agent = ConstraintValidatorAgent()
        self.mcp_tools = get_mcp_tools()
        self.last_generated_playlist: Optional[GeneratedPlaylist] = None
        self.dj_email = "dj@local"  # default, puede ser sobrescrito
        self.user_id = "anonymous"  # Para rate limiting

    def should_validate_constraints(self, constraints: ParsedConstraints) -> bool:
        """Decide si se necesita validación avanzada (subagent)"""
        # Triggers: fases múltiples, restricciones complejas o ambigüedad
        return (
            constraints.phases is not None or
            constraints.no_artist_repeat or
            constraints.max_artist_repeats < 999
        )

    def process_tool_call(self, tool_name: str, tool_input: Dict) -> str:
        """Ejecuta herramientas (MCP + locales) y retorna resultado"""
        # MCP Tools
        if tool_name in ["search_tracks", "get_track_metadata", "validate_catalog_feasibility", "get_catalog_stats"]:
            return process_mcp_tool_call(tool_name, tool_input)

        # Local tools
        elif tool_name == "parse_dj_request":
            constraints = parse_dj_request(tool_input["request_text"])
            return json.dumps({
                "dj_name": constraints.dj_name,
                "duration_minutes": constraints.duration_minutes,
                "bpm_start": constraints.bpm_start,
                "bpm_end": constraints.bpm_end,
                "tonalities": constraints.tonalities,
                "no_artist_repeat": constraints.no_artist_repeat,
                "max_artist_repeats": constraints.max_artist_repeats,
                "genre": constraints.genre,
                "phases": constraints.phases
            })

        elif tool_name == "build_playlist":
            constraints_dict = json.loads(tool_input["constraints_json"])
            # Filter to only expected fields
            valid_fields = {
                "dj_name", "duration_minutes", "bpm_start", "bpm_end",
                "tonalities", "no_artist_repeat", "max_artist_repeats",
                "genre", "phases"
            }
            filtered_dict = {k: v for k, v in constraints_dict.items() if k in valid_fields}
            constraints = ParsedConstraints(**filtered_dict)

            def search_provider(bpm_min, bpm_max, tonalities, exclude_artists=None, exclude_ids=None):
                result_str = process_mcp_tool_call("search_tracks", {
                    "bpm_min": bpm_min,
                    "bpm_max": bpm_max,
                    "tonalities": tonalities,
                    "exclude_artists": exclude_artists,
                    "exclude_ids": exclude_ids
                })
                return json.loads(result_str)

            playlist = build_playlist_greedy(constraints, search_provider)
            if playlist:
                # Guardar en memoria para checkpoint posterior
                if constraints.phases:
                    # Multi-fase: dividir playlist en 2 partes iguales
                    mid = len(playlist) // 2
                    phase_1 = playlist[:mid]
                    phase_2 = playlist[mid:]

                    # Store stats en phase_1 y phase_2 para diagnostico
                    phase_1_duration = sum(t.get("duration", 0) for t in phase_1)
                    phase_2_duration = sum(t.get("duration", 0) for t in phase_2)

                    self.last_generated_playlist = GeneratedPlaylist(
                        phase_1_tracks=phase_1,
                        phase_2_tracks=phase_2
                    )
                    # Print diagnostic
                    print(f"\n📊 Multi-fase compilado:")
                    print(f"   Fase 1: {len(phase_1)} tracks, {phase_1_duration:.1f} min")
                    print(f"   Fase 2: {len(phase_2)} tracks, {phase_2_duration:.1f} min")
                else:
                    # Single-phase
                    self.last_generated_playlist = GeneratedPlaylist(playlist_tracks=playlist)
                return json.dumps(playlist)
            else:
                return json.dumps({"error": "No se pudo construir playlist"})

        elif tool_name == "explain_playlist":
            playlist = json.loads(tool_input["playlist_json"])
            constraints_dict = json.loads(tool_input["constraints_json"])
            # Filter to only expected fields
            valid_fields = {
                "dj_name", "duration_minutes", "bpm_start", "bpm_end",
                "tonalities", "no_artist_repeat", "max_artist_repeats",
                "genre", "phases"
            }
            filtered_dict = {k: v for k, v in constraints_dict.items() if k in valid_fields}
            constraints = ParsedConstraints(**filtered_dict)
            explanation = explain_playlist(playlist, constraints)
            return explanation

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def run(self, dj_request: str) -> str:
        """Ejecuta el agente con una solicitud de DJ"""
        # RATE LIMITING CHECK
        allowed, msg = self._rate_limiter.check_rate_limit(self.user_id)
        if not allowed:
            print(f"\n{msg}")
            return msg

        print(f"\n🎤 DJ REQUEST:\n{dj_request}\n")
        print("=" * 70)

        # Paso 1: Parse local
        parsed = parse_dj_request(dj_request)
        print(f"📊 Constraints parsed: {parsed.duration_minutes}min, {parsed.bpm_start}-{parsed.bpm_end} BPM")

        # Paso 2: Validar con subagent si es complejo
        if self.should_validate_constraints(parsed):
            print("🤖 Constraints complejas detectadas → Invocando subagent validator...")

            constraints_dict = {
                "dj_name": parsed.dj_name,
                "duration_minutes": parsed.duration_minutes,
                "bpm_start": parsed.bpm_start,
                "bpm_end": parsed.bpm_end,
                "tonalities": parsed.tonalities,
                "no_artist_repeat": parsed.no_artist_repeat,
                "max_artist_repeats": parsed.max_artist_repeats,
                "genre": parsed.genre
            }

            # Llamar a MCP para validación de viabilidad
            catalog_feedback_str = process_mcp_tool_call("validate_catalog_feasibility", {
                "bpm_start": parsed.bpm_start,
                "bpm_end": parsed.bpm_end,
                "tonalities": parsed.tonalities,
                "duration_minutes": parsed.duration_minutes,
                "no_artist_repeat": parsed.no_artist_repeat
            })
            catalog_feedback = json.loads(catalog_feedback_str)

            # Validator subagent
            validation_result = self.validator_agent.validate_and_negotiate(
                constraints_dict,
                catalog_feedback
            )

            print(f"✅ Validator result: {validation_result.explanation}")
            if validation_result.adjustments_made:
                print(f"   Adjustments: {validation_result.adjustments_made}")

            parsed.bpm_start = validation_result.refined_constraints.get("bpm_start", parsed.bpm_start)
            parsed.bpm_end = validation_result.refined_constraints.get("bpm_end", parsed.bpm_end)
            parsed.duration_minutes = validation_result.refined_constraints.get("duration_minutes", parsed.duration_minutes)

        # Paso 3: Agentic loop principal con Claude
        all_tools = [
            {
                "name": "parse_dj_request",
                "description": "Parsea solicitud de DJ a restricciones normalizadas",
                "input_schema": {
                    "type": "object",
                    "properties": {"request_text": {"type": "string"}},
                    "required": ["request_text"]
                }
            },
            {
                "name": "build_playlist",
                "description": "Construye playlist optimizada",
                "input_schema": {
                    "type": "object",
                    "properties": {"constraints_json": {"type": "string"}},
                    "required": ["constraints_json"]
                }
            },
            {
                "name": "explain_playlist",
                "description": "Explica la playlist generada",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "playlist_json": {"type": "string"},
                        "constraints_json": {"type": "string"}
                    },
                    "required": ["playlist_json", "constraints_json"]
                }
            }
        ] + self.mcp_tools

        self.conversation_history = [
            {
                "role": "user",
                "content": f"""Eres un agente DJ Playlist Generator.

Solicitud: {dj_request}

Usa las herramientas para:
1. Parsear/validar restricciones
2. Consultar catálogo (MCP)
3. Construir playlist
4. Explicar decisiones

Sé conciso y directo."""
            }
        ]

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=all_tools,
                messages=self.conversation_history
            )

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"\n📋 AGENT RESPONSE:\n{block.text}")
                break

            elif response.stop_reason == "tool_use":
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"🔧 Tool: {block.name}")
                        result = self.process_tool_call(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                break

        # Paso 4: CHECKPOINT - Si hay playlist generada, guardar propuesta
        if self.last_generated_playlist:
            self._create_checkpoint(parsed)

        return "Done"

    def _create_checkpoint(self, constraints: ParsedConstraints):
        """Crea checkpoint para aprobación del PM"""
        print("\n" + "=" * 70)
        print("🔐 CHECKPOINT: ESPERANDO APROBACIÓN DEL DJ")
        print("=" * 70)

        result_str = process_mcp_tool_call("save_playlist_proposal", {
            "dj_name": constraints.dj_name,
            "dj_email": self.dj_email,
            "constraints": {
                "duration_minutes": constraints.duration_minutes,
                "bpm_start": constraints.bpm_start,
                "bpm_end": constraints.bpm_end,
                "tonalities": constraints.tonalities,
                "no_artist_repeat": constraints.no_artist_repeat,
                "genre": constraints.genre
            },
            "playlist_tracks": self.last_generated_playlist.playlist_tracks or [],
            "phase_1_tracks": self.last_generated_playlist.phase_1_tracks,
            "phase_2_tracks": self.last_generated_playlist.phase_2_tracks
        })

        result = json.loads(result_str)
        if result.get("success"):
            print(f"\n✅ Propuesta guardada: {result['proposal_id']}")
            print(f"\n🔗 CHECKPOINT URL:\n{result['checkpoint_url']}")
            print(f"\n📋 RESUMEN:\n{result['summary']}")
            print(f"\n⏰ Expira en: {result['expires_at']}")
            print("\n" + "=" * 70)
            print("⏸️  AGENTE EN ESPERA DE APROBACIÓN DEL DJ")
            print("=" * 70)
        else:
            print(f"❌ Error al guardar propuesta: {result.get('error')}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    agent = DJPlaylistAgent()

    # Test case 1: Clean request
    request = """DJ: María
Duración: 45 minutos
BPM: Empezar en 115, subir progresivamente a 128
Tonos: Armónicos compatibles (Do Mayor familia)
Restricción extra: Sin repetir artistas
Género: House/Tech House"""

    agent.run(request)

"""Rate limiting y guardrails para el agente"""

import time
from collections import defaultdict
from typing import Dict, List
from datetime import datetime, timedelta


class RateLimiter:
    """Implementa límites de solicitudes por sesión y per-user"""

    def __init__(self, max_per_session: int = 10, min_interval_seconds: float = 10.0):
        self.max_per_session = max_per_session
        self.min_interval_seconds = min_interval_seconds
        self.request_times: Dict[str, List[float]] = defaultdict()  # user_id → [timestamps]
        self.last_request_time: Dict[str, float] = defaultdict()

    def check_rate_limit(self, user_id: str) -> tuple[bool, str]:
        """
        Verifica si usuario puede hacer solicitud.
        Retorna: (allowed: bool, message: str)
        """
        now = time.time()

        # Inicializar si no existe
        if user_id not in self.request_times:
            self.request_times[user_id] = []
            self.last_request_time[user_id] = 0

        # Limpiar requests antiguos (> 1 día)
        cutoff = now - (24 * 3600)
        self.request_times[user_id] = [t for t in self.request_times[user_id] if t > cutoff]

        # Check 1: Max requests per session
        if len(self.request_times[user_id]) >= self.max_per_session:
            return False, f"❌ Límite alcanzado: {self.max_per_session} solicitudes por sesión (24h)"

        # Check 2: Min interval between requests
        time_since_last = now - self.last_request_time[user_id]
        if time_since_last < self.min_interval_seconds:
            wait_time = int(self.min_interval_seconds - time_since_last)
            return False, f"⏱️  Espera {wait_time}s antes de siguiente solicitud (mín {self.min_interval_seconds}s)"

        # OK
        self.request_times[user_id].append(now)
        self.last_request_time[user_id] = now
        remaining = self.max_per_session - len(self.request_times[user_id])
        return True, f"✅ Solicitud permitida ({remaining} restantes hoy)"

    def get_stats(self, user_id: str) -> Dict:
        """Retorna estadísticas de uso"""
        return {
            "user_id": user_id,
            "requests_today": len(self.request_times.get(user_id, [])),
            "max_per_session": self.max_per_session,
            "last_request_at": datetime.fromtimestamp(self.last_request_time.get(user_id, 0)).isoformat() if self.last_request_time.get(user_id, 0) else None
        }


class OutputGuardrails:
    """Valida que output no contenga datos sensibles o inválidos"""

    SENSITIVE_PATTERNS = [
        r"\$\d+",  # Dinero
        r"\b\d{16}\b",  # Credit card like
        r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",  # Email
    ]

    INVALID_ID_PATTERNS = [
        r"track_id.*null",
        r"id.*-1",
        r"id.*999999",
    ]

    @staticmethod
    def validate_playlist_json(playlist: Dict) -> tuple[bool, List[str]]:
        """
        Valida playlist antes de exponerlo.
        Retorna: (valid: bool, issues: List[str])

        Soporta:
        - Single-phase: {tracks: [...]}
        - Multi-fase: {phase_1: {tracks: [...]}, phase_2: {tracks: [...]}}
        - Legacy: {playlist_tracks: [...]}
        """
        issues = []

        # Extrae tracks según formato
        if isinstance(playlist, list):
            tracks = playlist
        elif playlist.get("phase_1") or playlist.get("phase_2"):
            # Multi-fase: combina tracks de ambas fases
            p1_tracks = playlist.get("phase_1", {}).get("tracks", []) if isinstance(playlist.get("phase_1"), dict) else []
            p2_tracks = playlist.get("phase_2", {}).get("tracks", []) if isinstance(playlist.get("phase_2"), dict) else []
            tracks = p1_tracks + p2_tracks
        else:
            # Single-phase
            tracks = (playlist.get("tracks") or
                     playlist.get("playlist") or
                     playlist.get("playlist_tracks") or
                     playlist.get("phase_1_tracks") or
                     playlist.get("phase_2_tracks") or [])

        if not tracks:
            issues.append("❌ Playlist vacía")

        # Valida cada track
        for i, track in enumerate(tracks if isinstance(tracks, list) else []):
            # Verifica que track_id sea válido
            track_id = track.get("id")
            if track_id is None:
                issues.append(f"❌ Track {i}: id es null")
            elif not isinstance(track_id, int) or track_id < 1:
                issues.append(f"❌ Track {i}: id inválido ({track_id})")

            # Verifica que BPM sea razonable
            bpm = track.get("bpm")
            if bpm is None or not (80 <= bpm <= 180):
                issues.append(f"❌ Track {i}: BPM fuera de rango ({bpm})")

            # Verifica que duración sea válida
            duration = track.get("duration")
            if duration is None or not (1 <= duration <= 20):
                issues.append(f"❌ Track {i}: duración inválida ({duration})")

        return len(issues) == 0, issues

    @staticmethod
    def strip_sensitive_data(text: str) -> str:
        """Remueve datos sensibles de texto"""
        import re
        for pattern in OutputGuardrails.SENSITIVE_PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text)
        return text

    @staticmethod
    def validate_no_promises(explanation: str) -> tuple[bool, str]:
        """Verifica que explanation no contenga promesas futuras"""
        import re

        future_markers = [
            r"mañana",
            r"próxima\s+semana",
            r"el\s+próximo",
            r"luego",
            r"después",
            r"will do",
            r"voy a hacer",
        ]

        for marker in future_markers:
            if re.search(marker, explanation.lower()):
                return False, f"⚠️  Explanation contiene promesa futura: '{marker}'"

        return True, "✅ OK (sin promesas)"

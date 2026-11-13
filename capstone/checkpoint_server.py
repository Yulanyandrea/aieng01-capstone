#!/usr/bin/env python3
"""
Checkpoint HTTP Server
Expone endpoint para que PM apruebe/rechace propuestas
"""

from flask import Flask, request, jsonify, render_template_string
from proposal_storage import ProposalStorage, generate_proposal_summary
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)

# HTML template para checkpoint UI
CHECKPOINT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DJ Playlist Checkpoint</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
        .status.approved { background: #d4edda; color: #155724; }
        .status.rejected { background: #f8d7da; color: #721c24; }
        .status.pending { background: #cce5ff; color: #004085; }
        .playlist { border: 1px solid #ddd; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .track { padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }
        .track:last-child { border-bottom: none; }
        button { padding: 10px 20px; margin: 5px; font-size: 16px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-approve { background: #28a745; color: white; }
        .btn-reject { background: #dc3545; color: white; }
        .btn-approve:hover { background: #218838; }
        .btn-reject:hover { background: #c82333; }
        .error { color: #721c24; background: #f8d7da; padding: 10px; border-radius: 4px; }
        .controls { display: flex; gap: 10px; margin: 20px 0; }
        textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: Arial; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 DJ Playlist Checkpoint</h1>

        {% if error %}
            <div class="error">{{ error }}</div>
        {% elif proposal %}
            <div class="status {{ proposal.status }}">
                <strong>Status:</strong> {{ proposal.status.upper() }}
                (Created: {{ proposal.created_at }}, Expires: {{ proposal.expires_at }})
            </div>

            <h2>Propuesta: {{ proposal.proposal_id }}</h2>

            <div class="playlist">
                <h3>Restricciones</h3>
                <pre>{{ constraints_text }}</pre>
            </div>

            {% if tracks %}
                <div class="playlist">
                    <h3>Tracks ({{ tracks|length }})</h3>
                    {% for track in tracks %}
                        <div class="track">
                            <span><strong>{{ loop.index }}.</strong> {{ track.artist }} - {{ track.title }}</span>
                            <span>{{ track.bpm }} BPM | {{ track.tonality }} | {{ track.duration }}min</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}

            {% if proposal.status == 'pending_approval' %}
                <div class="controls">
                    <button class="btn-approve" onclick="approveProposal()">✅ Approve</button>
                    <button class="btn-reject" onclick="rejectProposal()">❌ Reject</button>
                </div>
                <textarea id="feedback" rows="3" placeholder="Optional feedback (en/es)"></textarea>
            {% endif %}

            {% if proposal.feedback %}
                <div style="margin-top: 10px; padding: 10px; background: #f0f0f0; border-radius: 4px;">
                    <strong>Feedback:</strong> {{ proposal.feedback }}
                </div>
            {% endif %}
        {% endif %}
    </div>

    <script>
        function approveProposal() {
            const feedback = document.getElementById('feedback')?.value || '';
            fetch('{{ checkpoint_url }}/approve', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({feedback})
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    alert('✅ Propuesta aprobada');
                    location.reload();
                } else {
                    alert('❌ Error: ' + data.error);
                }
            });
        }
        function rejectProposal() {
            if (!confirm('¿Rechazar propuesta?')) return;
            const feedback = document.getElementById('feedback')?.value || '';
            fetch('{{ checkpoint_url }}/reject', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({feedback})
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    alert('❌ Propuesta rechazada');
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/checkpoint/<proposal_id>', methods=['GET'])
def view_checkpoint(proposal_id: str):
    """Vista de checkpoint para PM"""
    token = request.args.get('token')

    proposal = ProposalStorage.get_proposal(proposal_id)
    if not proposal:
        return render_template_string(CHECKPOINT_TEMPLATE, error="Propuesta no encontrada o expirada"), 404

    # Extrae tracks
    tracks = proposal.phase_1_tracks or proposal.phase_2_tracks or proposal.playlist_tracks or []

    constraints_text = json.dumps(proposal.constraints, indent=2, ensure_ascii=False)

    return render_template_string(
        CHECKPOINT_TEMPLATE,
        proposal=proposal.to_public_dict(),
        tracks=tracks,
        constraints_text=constraints_text,
        checkpoint_url=f'/checkpoint/{proposal_id}'
    )


@app.route('/checkpoint/<proposal_id>/approve', methods=['POST'])
def approve_checkpoint(proposal_id: str):
    """Aprueba propuesta"""
    data = request.json or {}
    feedback = data.get('feedback', '')
    token = request.headers.get('X-Approval-Token')

    # En MVP, no validamos token (TODO: extractr de sesión)
    proposal = ProposalStorage.get_proposal(proposal_id)
    if not proposal:
        return jsonify({"error": "Proposal not found"}), 404

    # Aprobación sin token check (MVP)
    ProposalStorage.approve_proposal(proposal_id, proposal.approval_token, feedback)

    return jsonify({"success": True, "proposal_id": proposal_id})


@app.route('/checkpoint/<proposal_id>/reject', methods=['POST'])
def reject_checkpoint(proposal_id: str):
    """Rechaza propuesta"""
    data = request.json or {}
    feedback = data.get('feedback', '')

    proposal = ProposalStorage.get_proposal(proposal_id)
    if not proposal:
        return jsonify({"error": "Proposal not found"}), 404

    ProposalStorage.reject_proposal(proposal_id, proposal.approval_token, feedback)

    return jsonify({"success": True, "proposal_id": proposal_id})


@app.route('/proposals', methods=['GET'])
def list_proposals():
    """Lista todas propuestas (debug)"""
    dj_email = request.args.get('dj_email')
    if dj_email:
        proposals = ProposalStorage.list_proposals_by_dj(dj_email)
    else:
        proposals = []
    return jsonify(proposals)


@app.route('/finalize/<proposal_id>', methods=['POST'])
def finalize_playlist(proposal_id: str):
    """
    Finaliza propuesta aprobada → genera JSON output.
    Solo funciona si status == 'approved'
    """
    proposal = ProposalStorage.get_proposal(proposal_id)
    if not proposal:
        return jsonify({"error": "Propuesta no encontrada o expirada"}), 404

    if proposal.status != 'approved':
        return jsonify({"error": f"Propuesta no aprobada (status: {proposal.status})"}), 400

    # Extrae tracks (puede ser single-phase o multi-fase)
    if proposal.phase_1_tracks or proposal.phase_2_tracks:
        # Multi-fase
        output = {
            "proposal_id": proposal_id,
            "dj": proposal.dj_name,
            "phase_1": {
                "tracks": proposal.phase_1_tracks or [],
                "duration": sum(t.get("duration", 0) for t in (proposal.phase_1_tracks or [])),
                "bpm_range": _get_bpm_range(proposal.phase_1_tracks or [])
            },
            "phase_2": {
                "tracks": proposal.phase_2_tracks or [],
                "duration": sum(t.get("duration", 0) for t in (proposal.phase_2_tracks or [])),
                "bpm_range": _get_bpm_range(proposal.phase_2_tracks or [])
            },
            "constraints": proposal.constraints,
            "status": "finalized",
            "approved_at": proposal.approved_at,
            "finalized_at": datetime.utcnow().isoformat(),
            "feedback": proposal.feedback
        }
    else:
        # Single-phase
        tracks = proposal.playlist_tracks or []
        output = {
            "proposal_id": proposal_id,
            "dj": proposal.dj_name,
            "tracks": tracks,
            "duration": sum(t.get("duration", 0) for t in tracks),
            "bpm_range": _get_bpm_range(tracks),
            "constraints": proposal.constraints,
            "status": "finalized",
            "approved_at": proposal.approved_at,
            "finalized_at": datetime.utcnow().isoformat(),
            "feedback": proposal.feedback
        }

    # Validar con guardrails
    from rate_limiter import OutputGuardrails
    valid, issues = OutputGuardrails.validate_playlist_json(output)
    if not valid:
        return jsonify({
            "error": "Output validation failed",
            "issues": issues
        }), 500

    return jsonify(output)


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok"})


def _get_bpm_range(tracks: list) -> dict:
    """Extrae rango BPM de tracks"""
    if not tracks:
        return {"min": 0, "max": 0}
    bpms = [t.get("bpm", 0) for t in tracks]
    return {"min": min(bpms), "max": max(bpms)}


if __name__ == '__main__':
    print("🌐 Checkpoint Server starting on http://localhost:8000")
    print("   View proposals: http://localhost:8000/proposals")
    app.run(host='0.0.0.0', port=8000, debug=True)

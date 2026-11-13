# Next Steps: Post-MVP Roadmap

## Phase 1: Finalize Endpoint (< 1h)

### Goal
After DJ/PM approves propuesta, generate final JSON output.

### Implementation
```python
# finalize_service.py (NEW)
@app.route('/finalize/<proposal_id>', methods=['POST'])
def finalize_playlist(proposal_id):
    proposal = ProposalStorage.get_proposal(proposal_id)
    if proposal.status != 'approved':
        return error("Not approved")
    
    # Generate final JSON
    output = {
        "proposal_id": proposal_id,
        "dj": proposal.dj_name,
        "tracks": proposal.playlist_tracks,
        "constraints": proposal.constraints,
        "approved_at": proposal.approved_at,
        "generated_at": datetime.now().isoformat()
    }
    
    # Validate with guardrails
    valid, issues = OutputGuardrails.validate_playlist_json(output)
    if not valid:
        return error(f"Validation failed: {issues}")
    
    return jsonify(output)
```

### Tests
```bash
# Approve propuesta, then finalize
POST /finalize/prop_00001
→ JSON with tracks
```

---

## Phase 2: PostgreSQL (2-3h)

### Goal
Persistence beyond 24h, durability, scale.

### Implementation
```python
# proposal_storage.py — Replace in-memory with SQLAlchemy
from sqlalchemy import create_engine, Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ProposalRecord(Base):
    __tablename__ = 'proposals'
    
    proposal_id = Column(String, primary_key=True)
    dj_name = Column(String)
    dj_email = Column(String)
    constraints = Column(JSON)
    playlist_tracks = Column(JSON)
    phase_1_tracks = Column(JSON, nullable=True)
    phase_2_tracks = Column(JSON, nullable=True)
    status = Column(String)  # pending, approved, rejected
    created_at = Column(DateTime)
    approved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime)
    approval_token = Column(String, unique=True)
    feedback = Column(String)

# Replace ProposalStorage in-memory dict with DB queries
class ProposalStorage:
    @staticmethod
    def save_proposal(proposal: PlaylistProposal) -> str:
        db.session.add(ProposalRecord(...))
        db.session.commit()
        return proposal_id
```

### Migration
```bash
# Create DB
createdb dj_playlist_generator

# Initialize schema
alembic upgrade head

# Run tests
python3 -m pytest test_*.py
```

---

## Phase 3: Spotify Integration (4-6h)

### Goal
Replace mock catalog with real Spotify tracks.

### Implementation
```python
# spotify_service.py (NEW)
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyService:
    def __init__(self, client_id, client_secret):
        self.sp = Spotify(auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        ))
    
    def search_by_bpm_tonality(self, bpm_min, bpm_max, tonalities, limit=50):
        # Use Spotify API to find tracks
        # BPM/tonality from Spotify audio features + Essentia analysis
        
        tracks = []
        for query in self.build_queries(tonalities):
            results = self.sp.search(q=query, type='track', limit=50)
            for track in results['tracks']['items']:
                # Get audio features (BPM, key, etc)
                audio = self.sp.audio_features(track['id'])[0]
                
                if bpm_min <= audio['tempo'] <= bpm_max:
                    tracks.append({
                        'id': track['id'],
                        'artist': track['artists'][0]['name'],
                        'title': track['name'],
                        'bpm': int(audio['tempo']),
                        'tonality': self.pitch_to_tonality(audio['key']),
                        'duration': track['duration_ms'] / 1000 / 60,
                        'genre': 'House',  # from artist profile
                        'spotify_uri': track['uri']
                    })
        
        return tracks
    
    @staticmethod
    def pitch_to_tonality(pitch_class):
        # Map Spotify pitch (0-11) to tonality
        mapping = {
            0: 'C_major', 1: 'C#_major', 2: 'D_major',
            ...
        }
        return mapping.get(pitch_class, 'C_major')
```

### Configuration
```bash
# .env
SPOTIFY_CLIENT_ID=xxx
SPOTIFY_CLIENT_SECRET=xxx
```

### Tests
```python
# test_spotify_service.py
def test_search_by_bpm():
    service = SpotifyService(...)
    tracks = service.search_by_bpm_tonality(120, 130, ['C_major'])
    assert len(tracks) > 0
    assert all(120 <= t['bpm'] <= 130 for t in tracks)
```

---

## Phase 4: React UI (6-8h)

### Goal
PM dashboard to view, approve, reject proposals in bulk.

### Structure
```
frontend/
├── package.json
├── src/
│   ├── App.tsx
│   ├── pages/
│   │   ├── ProposalList.tsx
│   │   ├── ProposalDetail.tsx
│   │   └── Dashboard.tsx
│   ├── components/
│   │   ├── PlaylistPlayer.tsx
│   │   ├── ApprovalForm.tsx
│   │   └── StatsCard.tsx
│   └── services/
│       └── api.ts
└── public/
```

### Key Features
- **Proposal List** — Filter by DJ, status, date
- **Approval Detail** — View tracks, constraints, approve/reject
- **Dashboard** — Stats (total proposals, approval rate, avg time-to-approve)
- **Notifications** — Real-time updates (WebSocket)

### Technology
```bash
npm init -y
npm install react typescript react-router-dom axios zustand
npm install -D @types/react vite
```

### Endpoints Required
```
GET    /api/proposals                    # List all
GET    /api/proposals/{id}               # Detail
POST   /api/proposals/{id}/approve       # Approve
POST   /api/proposals/{id}/reject        # Reject
GET    /api/stats                        # Dashboard stats
WS     /api/proposals/stream             # WebSocket updates
```

---

## Phase 5: Testing & Validation (2-3h)

### Unit Tests
```bash
# Rate limiter
pytest test_rate_limiter.py

# Checkpoint flow
pytest test_checkpoint.py

# Proposals (DB)
pytest test_proposal_storage.py -m db

# Spotify integration
pytest test_spotify_service.py -m integration
```

### Integration Tests
```bash
# End-to-end flow
pytest test_e2e.py

# Multi-phase validation (request_03 golden set)
pytest test_request_03_golden.py
```

### Load Testing
```python
# locustfile.py
from locust import HttpUser, task, between

class PlaylistUser(HttpUser):
    wait_time = between(5, 10)
    
    @task
    def generate_playlist(self):
        self.client.post("/generate", json={
            "dj_name": "TestDJ",
            "duration": 45,
            ...
        })
```

---

## Timeline Estimate

| Phase | Hours | Priority |
|-------|-------|----------|
| 1. Finalize Endpoint | 1 | 🔴 Critical |
| 2. PostgreSQL | 3 | 🔴 Critical |
| 3. Spotify API | 5 | 🟡 Important |
| 4. React UI | 7 | 🟡 Important |
| 5. Testing | 3 | 🟢 Nice-to-have |
| **Total** | **19h** | |

---

## Quick Start (Next Session)

```bash
# 1. Start where you left off
cd /workshop/capstone
git log --oneline
# Shows: edfc39b Session summary (checkpoint complete)

# 2. Quick test to verify everything
python3 demo_full_flow.py

# 3. Start Phase 1: Finalize endpoint
# Implement in checkpoint_server.py or new finalize_service.py

# 4. Commit
git add -A
git commit -m "Add finalize endpoint"
```

---

## Notes for Next Dev

- **Rate limiter** is per-session (resets on app restart). For persistence, tie to user_id + DB
- **Proposal expiration** currently 24h. Consider making it configurable per deployment
- **Multi-phase** logic assumes 2 phases. Generalize if needed for 3+ phases
- **Spotify tonality mapping** may need fine-tuning (pitch_class → C major/minor)
- **Output guardrails** currently validate structure. Consider adding business logic validation (e.g., no more than 3 artists repeated)

---

## References

- Spotify API Docs: https://developer.spotify.com/documentation/web-api
- Audio Features (BPM, key): https://developer.spotify.com/documentation/web-api/reference/get-audio-features
- SQLAlchemy: https://docs.sqlalchemy.org/
- React Router: https://reactrouter.com/

---

**Status: 🟢 Ready for Phase 1 (Finalize Endpoint)**

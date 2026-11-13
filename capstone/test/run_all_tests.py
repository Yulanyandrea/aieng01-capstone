"""
Test runner para DJ Playlist Generator Agent
Ejecuta los 3 casos de entrada estándar + 1 adicional con conflicto
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentes.dj_agent import DJPlaylistAgent

# Load test cases
with open(str(Path(__file__).parent.parent / "ideacion/00-material/request_01_clean.txt"), "r") as f:
    REQUEST_01_CLEAN = f.read()

with open(str(Path(__file__).parent.parent / "ideacion/00-material/request_02_messy.txt"), "r") as f:
    REQUEST_02_MESSY = f.read()

with open(str(Path(__file__).parent.parent / "ideacion/00-material/request_03_complex.txt"), "r") as f:
    REQUEST_03_COMPLEX = f.read()

# Additional test case: conflicting constraints (justifies subagent)
REQUEST_04_CONFLICT = """DJ: Alex
Duración: 90 minutos
BPM: 110 a 115 (rango muy estrecho)
Tonos: Do Mayor y La Menor solamente
Restricción: Sin repetir artistas bajo ninguna circunstancia
Nota: Tengo 10 minutos, necesito esto YA"""

def run_test(test_name: str, request: str):
    """Ejecuta un test individual"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(request)
    print(f"{'='*80}\n")

    agent = DJPlaylistAgent()
    agent.run(request)

if __name__ == "__main__":
    print("\n🎵 DJ PLAYLIST GENERATOR - TEST SUITE\n")

    # Run all tests
    run_test("01 - Clean Request", REQUEST_01_CLEAN)
    run_test("02 - Messy Request", REQUEST_02_MESSY)
    run_test("03 - Complex Multi-Phase", REQUEST_03_COMPLEX)
    run_test("04 - Conflicting Constraints (tests subagent)", REQUEST_04_CONFLICT)

    print("\n✅ All tests completed!")

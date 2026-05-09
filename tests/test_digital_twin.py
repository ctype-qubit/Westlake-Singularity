"""
Test digital twin engine
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_comsol_bridge_creation():
    from digital_twin.engine import COMSOLBridge
    bridge = COMSOLBridge()
    assert bridge is not None
    assert bridge.list_models() == []

def test_comsol_simulated_solve():
    from digital_twin.engine import COMSOLBridge, comsol_bridge
    comsol_bridge.load_model("test_model", "test.mph", {"field_T": 8.0})
    result = comsol_bridge.solve("test_model")
    assert result["status"] in ("simulated", "ok")
    assert "results" in result

def test_sim_real_loop():
    from digital_twin.engine import SimToRealLoop, comsol_bridge
    loop = SimToRealLoop(comsol_bridge)
    assert loop.config.tolerance == 0.05
    assert loop.config.max_iterations == 10

"""
Test tool system
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_stm_controller():
    from tools.stm_controller import STMController, STMState
    stm = STMController()
    assert not stm.state.connected
    assert stm.state.temperature_K == 4.2

def test_nanonis_protocol():
    from tools.stm_controller import NanonisProtocol
    proto = NanonisProtocol()
    
    encoded = proto.encode("BIAS.SET", {"value": 0.5})
    assert b"BIAS.SET" in encoded
    
    decoded = proto.decode(b"status=ok\nbias=0.5\n")
    assert decoded.get("status") == "ok"

def test_dft_tool():
    from tools.dft_tool import DFTTool, DFTParams
    dft = DFTTool()
    params = DFTParams()
    
    incar = dft.generate_incar(params)
    assert "ENCUT" in incar
    assert "SYSTEM" in incar

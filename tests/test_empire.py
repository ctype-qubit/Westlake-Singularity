"""
Test empire layer
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_federation():
    from empire.manager import FederationManager
    fm = FederationManager("lab1", "Test Lab")
    fm.register_peer("lab2", {"name": "Peer Lab"})
    
    model = fm.create_model("test_model", {"param1": 1.0, "param2": 2.0})
    assert model.name == "test_model"
    
    result = fm.federated_average("test_model", {
        "lab2": {"param1": 0.8, "param2": 2.2}
    })
    assert result["status"] == "ok"
    assert result["version"] == 2

def test_knowledge_transfer():
    from empire.manager import KnowledgeTransfer
    kt = KnowledgeTransfer("lab1")
    
    pkg = kt.package_knowledge(
        "FeSe_gap_map", "condensed_matter",
        {"gap_meV": 3.5, "Tc_K": 14.5},
        tags=["FeSe", "superconductivity", "gap"]
    )
    assert pkg.domain == "condensed_matter"
    
    received = kt.receive_knowledge(
        pkg.to_transfer_format(anonymize=True),
        source_lab="partner_lab"
    )
    assert received.name == "FeSe_gap_map"

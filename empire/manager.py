"""
Westlake Singularity — 帝国层管理器
联邦学习、跨组知识迁移、科研外交
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""
import json, logging, time
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("singularity.empire")

@dataclass
class FederatedModel:
    name: str
    parameters: dict = field(default_factory=dict)
    version: int = 1
    contributors: list = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)

class FederationManager:
    def __init__(self, lab_id: str, lab_name: str):
        self.lab_id = lab_id
        self.lab_name = lab_name
        self._models: dict = {}
        self._peers: dict = {}
    
    def register_peer(self, lab_id: str, info: dict) -> None:
        self._peers[lab_id] = info
    
    def create_model(self, name: str, params: dict = None) -> FederatedModel:
        model = FederatedModel(name=name, parameters=params or {}, contributors=[self.lab_id])
        self._models[name] = model
        return model
    
    def federated_average(self, model_name: str, peer_updates: dict) -> dict:
        if model_name not in self._models:
            return {"status": "error", "message": f"Model {model_name} not found"}
        model = self._models[model_name]
        for param_name in model.parameters:
            values = [model.parameters[param_name]]
            for lab_id, updates in peer_updates.items():
                if param_name in updates:
                    values.append(updates[param_name])
            model.parameters[param_name] = sum(values) / len(values)
        model.version += 1
        model.contributors = list(set(model.contributors + list(peer_updates.keys())))
        model.last_updated = time.time()
        return {"status": "ok", "model": model_name, "version": model.version, "parameters": model.parameters}

@dataclass
class KnowledgePackage:
    name: str
    domain: str
    content: dict = field(default_factory=dict)
    source_lab: str = ""
    version: int = 1
    tags: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def to_transfer_format(self, anonymize: bool = False) -> dict:
        data = {"name": self.name, "domain": self.domain, "content": self.content, "version": self.version, "tags": self.tags}
        if not anonymize:
            data["source_lab"] = self.source_lab
        return data

class KnowledgeTransfer:
    def __init__(self, lab_id: str):
        self.lab_id = lab_id
        self._kb: dict = {}
    
    def package_knowledge(self, name: str, domain: str, content: dict, tags: list = None) -> KnowledgePackage:
        pkg = KnowledgePackage(name=name, domain=domain, content=content, source_lab=self.lab_id, tags=tags or [])
        self._kb[name] = pkg
        return pkg
    
    def receive_knowledge(self, data: dict, source_lab: str) -> KnowledgePackage:
        pkg = KnowledgePackage(name=data["name"], domain=data["domain"], content=data["content"], source_lab=source_lab, version=data.get("version", 1), tags=data.get("tags", []))
        self._kb[pkg.name] = pkg
        return pkg

class DiplomacyProtocol:
    def __init__(self):
        self._agreements: dict = {}
    
    def propose_agreement(self, peer_lab: str, resource_type: str, terms: dict) -> dict:
        aid = f"dipl_{peer_lab}_{int(time.time())}"
        self._agreements[aid] = {"id": aid, "peer": peer_lab, "type": resource_type, "terms": terms, "status": "proposed"}
        return {"status": "ok", "agreement_id": aid}

# Globals
federation = FederationManager("westlake-konglab", "Lingyuan Kong Lab, Westlake University")
knowledge_transfer = KnowledgeTransfer("westlake-konglab")
diplomacy = DiplomacyProtocol()

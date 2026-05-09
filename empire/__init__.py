"""
Westlake Singularity — 帝国层
联邦学习 + 跨组知识迁移 + 科研外交
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""
from .manager import (
    FederationManager, FederatedModel,
    KnowledgeTransfer, KnowledgePackage,
    DiplomacyProtocol,
    federation, knowledge_transfer, diplomacy,
)
__all__ = [
    "FederationManager", "FederatedModel",
    "KnowledgeTransfer", "KnowledgePackage", 
    "DiplomacyProtocol",
    "federation", "knowledge_transfer", "diplomacy",
]

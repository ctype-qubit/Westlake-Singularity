"""Westlake Singularity — Agent角色系统
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

from .base import BaseRole
from .guard import GuardRole
from .mapper import MapperRole
from .discovery import DiscoveryRole
from .orchestrator import OrchestratorRole
from .compute import ComputeRole
from .registry import RoleRegistry

__all__ = [
    "BaseRole",
    "GuardRole",
    "MapperRole", 
    "DiscoveryRole",
    "OrchestratorRole",
    "ComputeRole",
    "RoleRegistry",
]

__version__ = "0.1.0-alpha"
__author__ = "Jiaxiang Cong · Lingyuan Kong Lab · Westlake University"
__team__ = ["Jupiter", "Venus", "Mars", "Mercury", "Saturn"]

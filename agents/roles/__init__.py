"""Westlake Singularity — Agent角色系统
Developer: Westlake Singularity Contributors
"""

from .base import BaseRole, Message, MessageBus, Priority, Permission, AgentMessage, RoleState, ResourceQuota
from .guard import GuardRole
from .mapper import MapperRole
from .discovery import DiscoveryRole
from .orchestrator import OrchestratorRole
from .compute import ComputeRole
from .registry import RoleRegistry, registry

# Auto-register all built-in roles at import time
def _register_builtin_roles():
    """Register all built-in roles at import time."""
    builtins = [GuardRole, MapperRole, DiscoveryRole, OrchestratorRole, ComputeRole]
    for role_cls in builtins:
        if role_cls.role_name not in registry._roles:
            registry.register(role_cls)

_register_builtin_roles()

__all__ = [
    "BaseRole", "Message", "MessageBus", "AgentMessage",
    "Priority", "Permission", "RoleState", "ResourceQuota",
    "GuardRole",
    "MapperRole", 
    "DiscoveryRole",
    "OrchestratorRole",
    "ComputeRole",
    "RoleRegistry", "registry",
]

__version__ = "0.2.0"
__author__ = "Westlake Singularity Contributors"
__team__ = ["Jupiter", "Venus", "Mars", "Mercury", "Saturn"]

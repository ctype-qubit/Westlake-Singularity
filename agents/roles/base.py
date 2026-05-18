"""
Westlake Singularity — Agent角色系统
完整实现入口
Developer: Westlake Singularity Contributors
"""

from .base_full import (
    BaseRole, Message, MessageBus,
    Priority, Permission, RoleState, ResourceQuota,
)

# 向后兼容: 旧的AgentMessage别名
AgentMessage = Message

__all__ = [
    "BaseRole", "Message", "MessageBus", "AgentMessage",
    "Priority", "Permission", "RoleState", "ResourceQuota",
]

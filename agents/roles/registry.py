"""RoleRegistry — Agent角色注册表
管理所有已注册的Agent角色，支持动态发现和加载
Developer: Westlake Singularity Contributors
"""

from typing import Type, Optional
from .base import BaseRole

class RoleRegistry:
    """Agent角色注册表 — 单例"""
    
    _instance: Optional["RoleRegistry"] = None
    _roles: dict[str, Type[BaseRole]] = {}
    _instances: dict[str, BaseRole] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._roles = {}
            cls._instance._instances = {}
        return cls._instance
    
    def register(self, role_cls: Type[BaseRole]) -> None:
        """注册一个新角色类型"""
        role_name = role_cls.role_name
        self._roles[role_name] = role_cls
        print(f"[Registry] Registered role: {role_name} (perm={role_cls.permission_level.name})")
    
    def create(self, role_name: str, **kwargs) -> BaseRole:
        """创建并启动一个角色实例"""
        if role_name not in self._roles:
            raise ValueError(f"Unknown role: {role_name}. Available: {list(self._roles.keys())}")
        
        instance = self._roles[role_name](**kwargs)
        self._instances[instance.agent_id] = instance
        return instance
    
    def get(self, agent_id: str) -> Optional[BaseRole]:
        return self._instances.get(agent_id)
    
    def list_roles(self) -> list[str]:
        return list(self._roles.keys())
    
    def list_instances(self) -> dict[str, str]:
        return {rid: r.role_name for rid, r in self._instances.items()}
    
    def shutdown_all(self):
        for instance in self._instances.values():
            instance.stop()
        self._instances.clear()

# 全局注册表单例
registry = RoleRegistry()

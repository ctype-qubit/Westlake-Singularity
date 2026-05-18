"""OrchestratorRole — 中央控制Agent
任务DAG分解、资源仲裁、实验序列编排、跨Agent协调
Developer: Westlake Singularity Contributors
"""

import asyncio
from typing import Optional
from collections import defaultdict
from .base import BaseRole, AgentMessage, Priority, Permission

class OrchestratorRole(BaseRole):
    """中央控制Agent — 等级5完全控制
    
    职责:
    - 接收高层实验目标，分解为Agent任务DAG
    - 监控任务执行状态
    - 资源冲突仲裁
    - 实验结果汇总上报
    """
    
    role_name = "Orchestrator"
    permission_level = Permission.FULL_CONTROL
    allowed_tools = [
        "task_decompose", "resource_allocate", "schedule_create",
        "conflict_resolve", "result_aggregate", "report_generate",
    ]
    heartbeat_interval = 3.0
    
    def __init__(self, role_id: str = None):
        super().__init__(role_id)
        self.active_tasks: dict[str, dict] = {}
        self.agent_registry: dict[str, str] = {}  # agent_id -> role_name
        self.task_history: list[dict] = []
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        msg_type = msg.msg_type
        
        if msg_type == "heartbeat":
            self.agent_registry[msg.src_agent] = msg.payload.get("role", "unknown")
            return None
        
        elif msg_type == "discovery":
            return await self._handle_discovery(msg)
        
        elif msg_type == "alert":
            if msg.payload.get("action_required"):
                return await self._handle_critical_alert(msg)
            return None
        
        elif msg_type == "command":
            return await self._handle_command(msg)
        
        elif msg_type == "scan_result":
            self.task_history.append(msg.payload)
            return None
        
        return None
    
    async def _handle_discovery(self, msg: AgentMessage) -> AgentMessage:
        """处理Discovery的发现：调度Mapper进行高精度重扫"""
        task_id = f"rescan_{msg.payload.get('scan_id', 'unknown')}"
        self.active_tasks[task_id] = {
            "status": "scheduled",
            "trigger": "discovery",
            "params": msg.payload,
        }
        
        # 命令Mapper进行针对性扫描
        return AgentMessage(
            src_agent=self.agent_id,
            dst_agent="Mapper",
            msg_type="quality_feedback",
            priority=Priority.IMPORTANT,
            payload={
                "target_region_nm": [
                    msg.payload.get("region_of_interest", {}).get("x_start_nm", 0),
                    msg.payload.get("region_of_interest", {}).get("x_end_nm", 100),
                ],
                "reason": msg.payload.get("suggested_action", ""),
            },
        )
    
    async def _handle_critical_alert(self, msg: AgentMessage) -> AgentMessage:
        """处理紧急告警：通知所有Agent暂停"""
        self.active_tasks.clear()
        return AgentMessage(
            src_agent=self.agent_id,
            dst_agent="*",
            msg_type="command",
            priority=Priority.CRITICAL,
            payload={"action": "pause_all", "reason": msg.payload},
        )
    
    async def _handle_command(self, msg: AgentMessage) -> Optional[AgentMessage]:
        action = msg.payload.get("action", "")
        
        if action == "status":
            return AgentMessage(
                src_agent=self.agent_id,
                msg_type="status",
                payload={
                    "active_tasks": len(self.active_tasks),
                    "registered_agents": self.agent_registry,
                    "total_history": len(self.task_history),
                }
            )
        
        elif action == "start_experiment":
            experiment = msg.payload.get("experiment", {})
            return await self._start_experiment(experiment)
        
        return None
    
    async def _start_experiment(self, config: dict) -> AgentMessage:
        task_id = config.get("name", f"exp_{len(self.task_history)}")
        self.active_tasks[task_id] = {"status": "running", "config": config}
        
        # 第一步：命令Mapper开始扫描
        return AgentMessage(
            src_agent=self.agent_id,
            dst_agent="Mapper",
            msg_type="scan_request",
            priority=Priority.NORMAL,
            payload={"experiment": task_id, "params": config.get("stm_params", {})},
        )

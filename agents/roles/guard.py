"""GuardRole — 安全守护Agent
监控传感器阈值、异常报警、心跳检测、实验室安全
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

import asyncio
from typing import Optional
from .base import BaseRole, AgentMessage, Priority, Permission

class GuardRole(BaseRole):
    """安全守护Agent — 等级5完全控制
    
    职责:
    - 实时监控所有传感器数据流
    - 超过安全阈值立即报警
    - 在危险情况下可主动关闭实验
    - 维护Agent心跳检测
    """
    
    role_name = "Guard"
    permission_level = Permission.FULL_CONTROL
    allowed_tools = [
        "sensor_read", "alert_send", "emergency_stop",
        "log_write", "heartbeat_check",
    ]
    heartbeat_interval = 2.0  # 2秒心跳（最频繁）
    
    def __init__(self, role_id: str = None, 
                 temp_max: float = 300.0,     # 最高温度(K)
                 pressure_max: float = 1e5,    # 最高压力(Pa)
                 field_max: float = 14.0,      # 最高磁场(T)
                 laser_power_max: float = 0.1, # 最高激光功率(W)
                 vacuum_min: float = 1e-10,    # 最低真空度(mbar)
                 ):
        super().__init__(role_id)
        self.thresholds = {
            "temperature_K": temp_max,
            "pressure_Pa": pressure_max,
            "magnetic_field_T": field_max,
            "laser_power_W": laser_power_max,
            "vacuum_mbar": vacuum_min,
        }
        self._agent_heartbeats: dict[str, float] = {}
        self._alert_count = 0
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """处理传感器数据、心跳、命令"""
        msg_type = msg.msg_type
        
        if msg_type == "sensor_data":
            return await self._check_sensors(msg)
        elif msg_type == "heartbeat":
            self._agent_heartbeats[msg.src_role] = msg.timestamp
            return None
        elif msg_type == "command":
            if msg.payload.get("action") == "emergency_stop":
                return await self._emergency_stop(msg)
            elif msg.payload.get("action") == "status_report":
                return self._status_report()
        
        return None
    
    async def _check_sensors(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """检查传感器数据是否超阈值"""
        data = msg.payload.get("readings", {})
        alerts = []
        
        for sensor, value in data.items():
            if sensor in self.thresholds:
                if sensor == "vacuum_mbar":
                    if value > self.thresholds[sensor]:  # 真空度反向判断
                        alerts.append(f"⚠ {sensor}: {value:.2e} > {self.thresholds[sensor]:.2e}")
                else:
                    if value > self.thresholds[sensor]:
                        alerts.append(f"⚠ {sensor}: {value:.2f} > {self.thresholds[sensor]:.2f}")
        
        if alerts:
            self._alert_count += 1
            is_critical = any("temperature" in a or "magnetic" in a for a in alerts)
            return AgentMessage(
                src_role=self.role_id,
                dst_role="Orchestrator",
                msg_type="alert",
                priority=Priority.CRITICAL if is_critical else Priority.URGENT,
                payload={
                    "alerts": alerts,
                    "alert_count": self._alert_count,
                    "action_required": is_critical,
                },
            )
        return None
    
    async def _emergency_stop(self, msg: AgentMessage) -> AgentMessage:
        """紧急停机"""
        return AgentMessage(
            src_role=self.role_id,
            dst_role="*",  # 广播给所有Agent
            msg_type="alert",
            priority=Priority.CRITICAL,
            payload={
                "action": "emergency_stop",
                "reason": msg.payload.get("reason", "manual trigger"),
                "timestamp": msg.timestamp,
            },
        )
    
    def _status_report(self) -> AgentMessage:
        """生成安全状态报告"""
        stale_agents = [
            agent_id for agent_id, last_hb in self._agent_heartbeats.items()
            if (msg := last_hb) and (time := __import__("time").time()) - msg > 15
        ]
        return AgentMessage(
            src_role=self.role_id,
            dst_role="Orchestrator",
            msg_type="status",
            priority=Priority.NORMAL,
            payload={
                "alerts_today": self._alert_count,
                "agents_monitored": len(self._agent_heartbeats),
                "stale_agents": stale_agents,
                "thresholds": self.thresholds,
            },
        )

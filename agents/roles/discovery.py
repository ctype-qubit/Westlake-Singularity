"""DiscoveryRole — 异常发现Agent
相变检测、拓扑信号识别、异常模式发现、patc
h-clamp触发
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

from typing import Optional
from .base import BaseRole, AgentMessage, Priority, Permission

class DiscoveryRole(BaseRole):
    """异常发现Agent — 等级4修改实验
    
    职责:
    - 分析STM图像寻找新相、缺陷、拓扑特征
    - 检测超导能隙变化
    - 发现后触发Mapper优化和Orchestrator重调度
    """
    
    role_name = "Discovery"
    permission_level = Permission.MODIFY_EXPERIMENT
    allowed_tools = [
        "image_analyze", "phase_detect", "gap_measure",
        "anomaly_score", "feature_extract", "trigger_rescan",
    ]
    heartbeat_interval = 5.0
    
    def __init__(self, role_id: str = None,
                 anomaly_threshold: float = 0.85,
                 phase_transition_sensitivity: float = 0.7,
                 ):
        super().__init__(role_id)
        self.anomaly_threshold = anomaly_threshold
        self.phase_sensitivity = phase_transition_sensitivity
        self.discoveries: list[dict] = []
        self._anomaly_scores: list[float] = []
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        msg_type = msg.msg_type
        
        if msg_type == "scan_result":
            return await self._analyze_scan(msg)
        elif msg_type == "command":
            return await self._handle_command(msg)
        return None
    
    async def _analyze_scan(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """分析扫描结果，寻找异常"""
        quality = msg.payload.get("quality_score", 0)
        drift = msg.payload.get("drift_nm", 0)
        
        # 简化的异常评分
        import random, math
        noise_floor = 0.3
        anomaly_score = max(0, min(1, 
            quality * (1 - drift * 100) + random.uniform(-0.1, 0.1)
        ))
        self._anomaly_scores.append(anomaly_score)
        
        if anomaly_score < self.anomaly_threshold:
            return None  # 无异常
        
        # 发现异常！
        discovery = {
            "scan_id": msg.payload.get("scan_id"),
            "anomaly_score": round(anomaly_score, 3),
            "suggested_action": self._suggest_action(anomaly_score),
            "region_of_interest": self._estimate_roi(msg.payload),
        }
        self.discoveries.append(discovery)
        
        # 通知Orchestrator
        return AgentMessage(
            src_role=self.role_id,
            dst_role="Orchestrator",
            msg_type="discovery",
            priority=Priority.IMPORTANT,
            payload=discovery,
        )
    
    def _suggest_action(self, score: float) -> str:
        if score > 0.95:
            return "phase_transition_detected — trigger full characterization"
        elif score > 0.90:
            return "likely_defect — suggest higher resolution scan"
        else:
            return "anomaly_suspected — flag for review"
    
    def _estimate_roi(self, scan_data: dict) -> dict:
        params = scan_data.get("params", {})
        size = params.get("scan_range_nm", 100)
        return {
            "x_start_nm": size * 0.3,
            "x_end_nm": size * 0.7,
            "y_start_nm": size * 0.3,
            "y_end_nm": size * 0.7,
        }
    
    async def _handle_command(self, msg: AgentMessage) -> Optional[AgentMessage]:
        action = msg.payload.get("action", "")
        if action == "discovery_report":
            return AgentMessage(
                src_role=self.role_id,
                dst_role="Orchestrator",
                msg_type="report",
                payload={
                    "total_discoveries": len(self.discoveries),
                    "recent": self.discoveries[-5:],
                    "avg_anomaly_score": (
                        sum(self._anomaly_scores) / len(self._anomaly_scores)
                        if self._anomaly_scores else 0
                    ),
                }
            )
        return None

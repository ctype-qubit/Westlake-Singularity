"""MapperRole — STM成像专家Agent
扫描参数优化、图像质量评分、漂移矫正、特征提取
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

import asyncio
from typing import Optional
from .base import BaseRole, AgentMessage, Priority, Permission

class MapperRole(BaseRole):
    """STM成像专家 — 等级3工具控制
    
    职责:
    - 根据Discovery的反馈优化扫描参数
    - 实时评估图像质量（SNR、分辨率、漂移）
    - 自动漂移矫正
    - 特征区域识别和锁定
    """
    
    role_name = "Mapper"
    permission_level = Permission.CONTROL_TOOLS
    allowed_tools = [
        "stm_scan", "stm_bias_set", "stm_current_set",
        "stm_tip_approach", "image_quality_check",
        "drift_correction", "feature_detect",
    ]
    heartbeat_interval = 5.0
    
    def __init__(self, role_id: str = None,
                 scan_range_default: float = 100.0,  # nm
                 bias_default: float = 0.1,           # V
                 current_default: float = 100.0,      # pA
                 pixel_default: int = 512,
                 ):
        super().__init__(role_id)
        self.params = {
            "scan_range_nm": scan_range_default,
            "bias_V": bias_default,
            "current_pA": current_default,
            "pixels": pixel_default,
            "scan_speed_nm_s": 100.0,
        }
        self.last_quality_score: float = 0.0
        self.scan_count = 0
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        msg_type = msg.msg_type
        
        if msg_type == "scan_request":
            return await self._execute_scan(msg)
        elif msg_type == "quality_feedback":
            return await self._optimize_from_feedback(msg)
        elif msg_type == "command":
            if msg.payload.get("action") == "adjust_params":
                self._update_params(msg.payload.get("params", {}))
        
        return None
    
    async def _execute_scan(self, msg: AgentMessage) -> AgentMessage:
        """执行STM扫描（模拟）"""
        self.scan_count += 1
        # 模拟扫描结果
        import random
        quality = max(0.3, min(0.98, random.gauss(0.75, 0.1)))
        drift_nm = random.uniform(0.001, 0.05)
        snr = 10 * (quality ** 2)
        
        self.last_quality_score = quality
        
        return AgentMessage(
            src_role=self.role_id,
            dst_role="Discovery",
            msg_type="scan_result",
            priority=Priority.NORMAL,
            payload={
                "scan_id": self.scan_count,
                "params": dict(self.params),
                "quality_score": round(quality, 3),
                "drift_nm": round(drift_nm, 4),
                "snr_db": round(snr, 1),
                "timestamp": msg.timestamp,
            },
        )
    
    async def _optimize_from_feedback(self, msg: AgentMessage) -> AgentMessage:
        """根据Discovery的反馈优化扫描参数"""
        feedback = msg.payload
        if "target_region_nm" in feedback:
            region = feedback["target_region_nm"]
            self.params["scan_range_nm"] = max(10, min(500, abs(region[2] - region[0])))
        
        if "suggested_bias_V" in feedback:
            self.params["bias_V"] = feedback["suggested_bias_V"]
        
        return AgentMessage(
            src_role=self.role_id,
            dst_role="Orchestrator",
            msg_type="params_updated",
            priority=Priority.NORMAL,
            payload={"new_params": dict(self.params)},
        )
    
    def _update_params(self, new_params: dict):
        self.params.update({k: v for k, v in new_params.items() if k in self.params})

"""ComputeRole — 超算调度Agent
Slurm作业管理、vLLM推理、DFT计算对齐
Developer: Westlake Singularity Contributors
"""

import asyncio
from typing import Optional
from .base import BaseRole, AgentMessage, Priority, Permission

class ComputeRole(BaseRole):
    """超算调度Agent — 等级2工具控制
    
    职责:
    - Slurm作业提交和监控
    - vLLM模型推理服务管理
    - DFT计算(VASP/QE)输入文件生成和结果解析
    - 计算资源分配
    """
    
    role_name = "Compute"
    permission_level = Permission.CONTROL_TOOLS
    allowed_tools = [
        "slurm_submit", "slurm_status", "slurm_cancel",
        "vllm_start", "vllm_stop", "vllm_infer",
        "dft_input_gen", "dft_result_parse",
        "resource_query",
    ]
    heartbeat_interval = 10.0
    
    def __init__(self, role_id: str = None,
                 slurm_partition: str = "gpu",
                 slurm_qos: str = "normal",
                 ):
        super().__init__(role_id)
        self.slurm_config = {
            "partition": slurm_partition,
            "qos": slurm_qos,
            "default_time": "24:00:00",
            "default_gpus": 1,
        }
        self.active_jobs: dict[str, dict] = {}
        self.vllm_status: str = "stopped"
    
    async def handle_message(self, msg: AgentMessage) -> Optional[AgentMessage]:
        msg_type = msg.msg_type
        
        if msg_type == "command":
            return await self._handle_command(msg)
        elif msg_type == "dft_request":
            return await self._handle_dft(msg)
        elif msg_type == "inference_request":
            return await self._handle_inference(msg)
        
        return None
    
    async def _handle_command(self, msg: AgentMessage) -> Optional[AgentMessage]:
        action = msg.payload.get("action", "")
        
        if action == "submit_job":
            job_id = f"job_{len(self.active_jobs):04d}"
            self.active_jobs[job_id] = {
                "status": "PENDING",
                "script": msg.payload.get("script", ""),
                "submitted_at": msg.timestamp,
            }
            return AgentMessage(
                src_agent=self.agent_id,
                dst_agent=msg.src_agent,
                msg_type="job_submitted",
                payload={"job_id": job_id, "status": "PENDING"},
            )
        
        elif action == "job_status":
            job_id = msg.payload.get("job_id", "")
            job = self.active_jobs.get(job_id, {})
            return AgentMessage(
                src_agent=self.agent_id,
                msg_type="job_status",
                payload={"job_id": job_id, "status": job.get("status", "UNKNOWN")},
            )
        
        elif action == "start_vllm":
            self.vllm_status = "running"
            return AgentMessage(
                src_agent=self.agent_id,
                msg_type="vllm_status",
                payload={"status": "running", "model": msg.payload.get("model", "default")},
            )
        
        return None
    
    async def _handle_dft(self, msg: AgentMessage) -> AgentMessage:
        """处理DFT计算请求"""
        params = msg.payload.get("params", {})
        job_id = f"dft_{len(self.active_jobs):04d}"
        self.active_jobs[job_id] = {
            "status": "QUEUED",
            "type": "dft",
            "params": params,
        }
        return AgentMessage(
            src_agent=self.agent_id,
            dst_agent=msg.src_agent,
            msg_type="dft_queued",
            payload={"job_id": job_id, "status": "QUEUED"},
        )
    
    async def _handle_inference(self, msg: AgentMessage) -> AgentMessage:
        """处理LLM推理请求"""
        prompt = msg.payload.get("prompt", "")
        return AgentMessage(
            src_agent=self.agent_id,
            dst_agent=msg.src_agent,
            msg_type="inference_result",
            payload={
                "model": msg.payload.get("model", "vllm_default"),
                "status": "complete",
                # 实际推理结果由vLLM工具填充
            },
        )

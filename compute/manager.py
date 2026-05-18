"""
Westlake Singularity — 超算集成层
Slurm作业编排 + vLLM模型管理 + 资源调度
Developer: Westlake Singularity Contributors
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("singularity.compute")

@dataclass
class SlurmJob:
    """Slurm作业"""
    job_id: str = ""
    name: str = ""
    state: str = "UNKNOWN"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    partition: str = "gpu"
    nodes: int = 1
    cpus: int = 1
    gpus: int = 0
    memory_gb: int = 4
    walltime: str = "24:00:00"
    output_file: str = ""
    error_file: str = ""
    submit_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    exit_code: Optional[int] = None
    
    @property
    def runtime_s(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0

class SlurmManager:
    """Slurm作业管理器"""
    
    def __init__(self):
        self._jobs: dict[str, SlurmJob] = {}
        self._scripts_dir = Path("./slurm_scripts")
        self._scripts_dir.mkdir(exist_ok=True)
    
    def _run_command(self, cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
        """执行命令"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except FileNotFoundError:
            return -1, "", "Slurm commands not found (not on a cluster?)"
    
    def submit(self, script: str, job_name: str = "singularity_job",
               partition: str = "gpu", nodes: int = 1, cpus: int = 16,
               gpus: int = 1, memory_gb: int = 64, walltime: str = "24:00:00") -> dict:
        """提交Slurm作业"""
        
        # 生成SBATCH脚本
        script_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={cpus}
#SBATCH --gres=gpu:{gpus}
#SBATCH --mem={memory_gb}G
#SBATCH --time={walltime}
#SBATCH --output={job_name}_%j.out
#SBATCH --error={job_name}_%j.err

{script}
"""
        script_path = self._scripts_dir / f"{job_name}.sh"
        script_path.write_text(script_content)
        
        # 提交
        ret, stdout, stderr = self._run_command(["sbatch", str(script_path)])
        
        if ret == 0:
            job_id = stdout.strip().split()[-1]
            job = SlurmJob(
                job_id=job_id, name=job_name, state="PENDING",
                partition=partition, nodes=nodes, cpus=cpus,
                gpus=gpus, memory_gb=memory_gb, walltime=walltime,
            )
            self._jobs[job_id] = job
            log.info(f"Job submitted: {job_id} ({job_name})")
            return {"status": "ok", "job_id": job_id, "job_name": job_name}
        else:
            return {"status": "error", "message": stderr or stdout}
    
    def status(self, job_id: str) -> dict:
        """查询作业状态"""
        ret, stdout, _ = self._run_command([
            "sacct", "-j", job_id, "--format=JobID,State,Elapsed,NodeList,ExitCode",
            "--noheader", "-P"
        ])
        
        if ret != 0:
            return {"status": "error", "message": "sacct failed"}
        
        lines = stdout.strip().split("\n")
        if not lines:
            return {"status": "error", "message": f"Job {job_id} not found"}
        
        # 解析sacct输出
        parts = lines[0].split("|")
        state = parts[1] if len(parts) > 1 else "UNKNOWN"
        
        if job_id in self._jobs:
            self._jobs[job_id].state = state
        
        return {
            "status": "ok",
            "job_id": job_id,
            "state": state,
            "elapsed": parts[2] if len(parts) > 2 else "",
            "nodes": parts[3] if len(parts) > 3 else "",
        }
    
    def cancel(self, job_id: str) -> dict:
        """取消作业"""
        ret, stdout, stderr = self._run_command(["scancel", job_id])
        if ret == 0:
            if job_id in self._jobs:
                self._jobs[job_id].state = "CANCELLED"
            return {"status": "ok", "job_id": job_id, "cancelled": True}
        return {"status": "error", "message": stderr}
    
    def list_jobs(self, user: str = None) -> list[dict]:
        """列出队列中的作业"""
        cmd = ["squeue", "--format=%i|%j|%T|%u|%M|%R", "--noheader"]
        if user:
            cmd.extend(["-u", user])
        
        ret, stdout, _ = self._run_command(cmd)
        if ret != 0:
            return []
        
        jobs = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 5:
                jobs.append({
                    "job_id": parts[0], "name": parts[1],
                    "state": parts[2], "user": parts[3],
                    "time": parts[4],
                })
        return jobs
    
    def estimate_wait_time(self, partition: str = "gpu") -> dict:
        """估算排队等待时间"""
        # 启发式: 检查队列中PENDING作业数
        jobs = self.list_jobs()
        pending = [j for j in jobs if j.get("state") == "PENDING"]
        
        return {
            "pending_jobs": len(pending),
            "estimated_minutes": len(pending) * 2,  # 粗略估计
            "partition": partition,
        }

class VLLMManager:
    """vLLM模型推理服务管理"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._process = None
        self._running = False
        self._model_name = ""
    
    def start(self, model_path: str, gpu_memory_utilization: float = 0.90,
             max_model_len: int = None, tensor_parallel_size: int = 1,
             dtype: str = "auto", trust_remote_code: bool = True) -> dict:
        """启动vLLM服务"""
        if self._running:
            return {"status": "error", "message": "vLLM already running"}
        
        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model_path,
            "--host", self.host,
            "--port", str(self.port),
            "--gpu-memory-utilization", str(gpu_memory_utilization),
            "--tensor-parallel-size", str(tensor_parallel_size),
            "--dtype", dtype,
        ]
        
        if max_model_len:
            cmd.extend(["--max-model-len", str(max_model_len)])
        if trust_remote_code:
            cmd.append("--trust-remote-code")
        
        try:
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            self._model_name = model_path
            self._running = True
            log.info(f"vLLM started: {model_path} on {self.host}:{self.port}")
            return {"status": "ok", "model": model_path, "url": self.base_url}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def stop(self) -> dict:
        """停止vLLM服务"""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._running = False
        return {"status": "stopped"}
    
    async def health_check(self) -> bool:
        """检查vLLM是否就绪"""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False
    
    async def wait_until_ready(self, timeout: int = 300) -> bool:
        """等待vLLM就绪"""
        start = time.time()
        while time.time() - start < timeout:
            if await self.health_check():
                return True
            await asyncio.sleep(2)
        return False
    
    async def query(self, prompt: str, max_tokens: int = 256,
                   temperature: float = 0.7) -> dict:
        """调用vLLM推理"""
        import aiohttp
        
        payload = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    data = await resp.json()
                    return {
                        "status": "ok",
                        "response": data["choices"][0]["message"]["content"],
                        "usage": data.get("usage", {}),
                    }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_models(self) -> list[str]:
        """列出可用模型"""
        models_dir = Path(os.path.expanduser("~/models"))
        if models_dir.exists():
            return [d.name for d in models_dir.iterdir() if d.is_dir()]
        return []

# 单例
slurm = SlurmManager()
vllm = VLLMManager()

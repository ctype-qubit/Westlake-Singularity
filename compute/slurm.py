"""SlurmTool — Slurm作业调度
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

import subprocess
from typing import Optional

class SlurmTool:
    """Slurm作业管理器"""
    
    def __init__(self, partition: str = "gpu", qos: str = "normal"):
        self.partition = partition
        self.qos = qos
    
    def submit(self, script_path: str) -> dict:
        """提交作业"""
        try:
            result = subprocess.run(
                ["sbatch", "-p", self.partition, "--qos", self.qos, script_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                job_id = result.stdout.strip().split()[-1]
                return {"status": "ok", "job_id": job_id}
            return {"status": "error", "message": result.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def status(self, job_id: str) -> dict:
        """查询作业状态"""
        try:
            result = subprocess.run(
                ["sacct", "-j", job_id, "--format=JobID,State,Elapsed,NodeList", "--noheader", "-P"],
                capture_output=True, text=True, timeout=10
            )
            return {"status": "ok", "job_id": job_id, "raw": result.stdout.strip()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def cancel(self, job_id: str) -> dict:
        """取消作业"""
        try:
            subprocess.run(["scancel", job_id], capture_output=True, timeout=10)
            return {"status": "ok", "job_id": job_id, "cancelled": True}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def queue(self, user: str = None) -> list:
        """查看队列"""
        cmd = ["squeue", "--format=%i %j %T %u", "--noheader"]
        if user:
            cmd.extend(["-u", user])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            jobs = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    jobs.append({"id": parts[0], "name": parts[1], "state": parts[2], "user": parts[3]})
            return jobs
        except Exception:
            return []

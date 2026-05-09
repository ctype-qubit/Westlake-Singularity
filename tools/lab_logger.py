"""LabLogger — 实验室日志工具
自动记录所有Agent操作、实验结果、异常
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class LogEntry:
    timestamp: float = field(default_factory=time.time)
    level: str = "INFO"
    agent: str = ""
    action: str = ""
    details: dict = field(default_factory=dict)
    experiment_id: Optional[str] = None

class LabLogger:
    """实验室日志系统"""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: list[LogEntry] = []
        self._flush_interval = 10
        self._last_flush = time.time()
    
    def log(self, agent: str, action: str, level: str = "INFO", 
            details: dict = None, experiment_id: str = None):
        entry = LogEntry(
            agent=agent, action=action, level=level,
            details=details or {}, experiment_id=experiment_id,
        )
        self._buffer.append(entry)
        
        if time.time() - self._last_flush > self._flush_interval:
            self.flush()
    
    def flush(self):
        if not self._buffer:
            return
        
        date_str = time.strftime("%Y%m%d")
        log_file = self.log_dir / f"lab_{date_str}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            for entry in self._buffer:
                f.write(json.dumps({
                    "ts": entry.timestamp,
                    "level": entry.level,
                    "agent": entry.agent,
                    "action": entry.action,
                    "details": entry.details,
                    "exp": entry.experiment_id,
                }, ensure_ascii=False) + "\n")
        
        self._buffer.clear()
        self._last_flash = time.time()
    
    def query(self, agent: str = None, action: str = None, 
              level: str = None, limit: int = 100) -> list[dict]:
        """查询日志（简单实现）"""
        results = []
        for entry in reversed(self._buffer):
            if agent and entry.agent != agent:
                continue
            if action and action not in entry.action:
                continue
            results.append({
                "ts": entry.timestamp,
                "agent": entry.agent,
                "action": entry.action,
                "level": entry.level,
            })
            if len(results) >= limit:
                break
        return results

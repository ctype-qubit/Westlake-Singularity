"""EventBus — WebSocket事件总线
将Agent事件桥接到硬件控制、AR/VR叠加、灯光效果
Developer: Westlake Singularity Contributors
"""

import asyncio
import json
import time
from typing import Callable, Optional

class EventBus:
    """WebSocket事件总线 — Agent ↔ 硬件 ↔ UI"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9876):
        self.host = host
        self.port = port
        self._clients: set = set()
        self._handlers: dict[str, list[Callable]] = {}
        self._running = False
    
    def on(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def emit(self, event_type: str, data: dict) -> None:
        """发送事件给所有WebSocket客户端"""
        msg = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        })
        # 本地处理器
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(data)
            except Exception:
                pass
        for handler in self._handlers.get("*", []):
            try:
                await handler(data)
            except Exception:
                pass
    
    # ── 硬件事件类型 ──
    async def emit_discovery(self, details: dict) -> None:
        """新发现事件 → 灯光效果 + AR叠加"""
        await self.emit("lab.discovery", details)
    
    async def emit_alert(self, level: str, message: str) -> None:
        """告警事件 → 红色灯光 + OLED警告"""
        await self.emit("lab.alert", {"level": level, "message": message})
    
    async def emit_scan_complete(self, quality: float) -> None:
        """扫描完成事件 → 状态更新"""
        await self.emit("lab.scan_complete", {"quality": quality})
    
    async def emit_experiment_milestone(self, milestone: str) -> None:
        """实验里程碑 → 日志 + 通知"""
        await self.emit("lab.milestone", {"milestone": milestone})

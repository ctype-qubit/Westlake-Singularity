"""RealtimeTool — WebSocket实时流式工具
毫秒级反馈环路，支持STM数据流、传感器流
Developer: Westlake Singularity Contributors
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

@dataclass
class StreamConfig:
    """实时流配置"""
    buffer_size: int = 1024
    sample_rate_hz: float = 1000.0
    channels: list[str] = field(default_factory=lambda: ["topography", "current", "phase"])
    compression: str = "none"  # none | zlib | lz4

class RealtimeTool:
    """实时流式工具 — WebSocket连接管理"""
    
    def __init__(self, url: str = "ws://localhost:9876"):
        self.url = url
        self._ws = None
        self._handlers: dict[str, list[Callable]] = {}
        self._buffer: list[dict] = []
        self._running = False
        self.config = StreamConfig()
    
    async def connect(self) -> bool:
        """建立WebSocket连接"""
        try:
            import websockets
            self._ws = await websockets.connect(self.url)
            self._running = True
            asyncio.create_task(self._read_loop())
            return True
        except Exception as e:
            print(f"[RealtimeTool] Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        self._running = False
        if self._ws:
            await self._ws.close()
    
    def on_message(self, msg_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        if msg_type not in self._handlers:
            self._handlers[msg_type] = []
        self._handlers[msg_type].append(handler)
    
    async def send(self, data: dict) -> None:
        """发送消息"""
        if self._ws:
            await self._ws.send(json.dumps(data))
    
    async def _read_loop(self) -> None:
        """读取循环：接收实时数据流"""
        while self._running and self._ws:
            try:
                raw = await asyncio.wait_for(self._ws.recv(), timeout=1.0)
                msg = json.loads(raw)
                msg_type = msg.get("type", "unknown")
                
                # 缓存
                self._buffer.append(msg)
                if len(self._buffer) > self.config.buffer_size:
                    self._buffer = self._buffer[-self.config.buffer_size // 2:]
                
                # 分发给处理器
                for handler in self._handlers.get(msg_type, []):
                    try:
                        await handler(msg)
                    except Exception as e:
                        print(f"[RealtimeTool] Handler error: {e}")
                        
                for handler in self._handlers.get("*", []):
                    try:
                        await handler(msg)
                    except Exception:
                        pass
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[RealtimeTool] Read error: {e}")
                break
    
    def get_buffer(self, channel: str = None, n: int = 100) -> list:
        """获取缓冲数据"""
        if channel:
            return [m for m in self._buffer if m.get("channel") == channel][-n:]
        return self._buffer[-n:]
    
    def get_latest(self, channel: str) -> Optional[dict]:
        """获取最新一条数据"""
        for m in reversed(self._buffer):
            if m.get("channel") == channel:
                return m
        return None

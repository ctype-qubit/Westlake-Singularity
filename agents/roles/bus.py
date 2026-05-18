"""MessageBus — Agent消息总线
异步发布/订阅系统，支持广播和点对点消息
Developer: Westlake Singularity Contributors
"""

import asyncio
from typing import Optional
from .base import AgentMessage, Priority

class MessageBus:
    """异步消息总线 — 发布/订阅模式
    
    特性:
    - 广播消息: dst_role="" 或 "*"
    - 优先级队列
    - 消息持久化（可选）
    """
    
    def __init__(self, max_queue_size: int = 10000):
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._max_queue_size = max_queue_size
        self._message_log: list[dict] = []
        self._total_messages = 0
    
    async def publish(self, msg: AgentMessage) -> None:
        """发布消息"""
        self._total_messages += 1
        self._message_log.append({
            "id": msg.msg_id,
            "src": msg.src_agent,
            "dst": msg.dst_agent,
            "type": msg.msg_type,
            "priority": int(msg.priority),
            "time": msg.timestamp,
        })
        
        # 修剪日志
        if len(self._message_log) > 1000:
            self._message_log = self._message_log[-500:]
        
        if msg.dst_agent in ("", "*"):
            # 广播给所有订阅者
            for queue in self._subscribers.values():
                if queue.qsize() < self._max_queue_size:
                    await queue.put(msg)
        else:
            # 点对点
            if msg.dst_agent in self._subscribers:
                queue = self._subscribers[msg.dst_agent]
                if queue.qsize() < self._max_queue_size:
                    await queue.put(msg)
    
    def subscribe(self, role_id: str) -> asyncio.Queue:
        """订阅消息通道"""
        queue = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers[role_id] = queue
        return queue
    
    def unsubscribe(self, role_id: str) -> None:
        """取消订阅"""
        self._subscribers.pop(role_id, None)
    
    async def start(self, roles: list) -> None:
        """启动消息总线，连接所有角色"""
        for role in roles:
            # Initialize if needed (UNINITIALIZED → IDLE)
            if role.state.value == "uninitialized":
                await role.initialize()
            queue = self.subscribe(role.agent_id)
            role._message_queue = queue
            asyncio.create_task(role.start(self))
    
    @property
    def stats(self) -> dict:
        return {
            "total_messages": self._total_messages,
            "subscribers": len(self._subscribers),
            "recent_messages": len(self._message_log),
        }

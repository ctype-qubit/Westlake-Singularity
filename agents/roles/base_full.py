"""
Westlake Singularity — 完整角色基类
带状态机、优先级调度、资源管理、错误恢复
Copyright (c) 2026 Jiaxiang Cong, Lingyuan Kong Lab, Westlake University
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Optional, Union

log = logging.getLogger("singularity.role")

# ── 枚举 ──

class RoleState(Enum):
    """角色生命周期状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"           # 等待外部资源
    DEGRADED = "degraded"         # 降级运行
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"

class Priority(IntEnum):
    """消息优先级"""
    BACKGROUND = 0
    NORMAL = 1
    IMPORTANT = 2
    URGENT = 3
    CRITICAL = 4

class Permission(IntEnum):
    """权限等级"""
    NONE = 0
    READ_SENSORS = 1
    CONTROL_TOOLS = 2
    MODIFY_EXPERIMENT = 3
    SCHEDULE_RESOURCES = 4
    FULL_CONTROL = 5
    ADMIN = 6

# ── 消息结构 ──

@dataclass
class Message:
    """Agent间标准消息"""
    msg_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    src_agent: str = ""
    dst_agent: str = ""          # ""=广播 "*"=所有
    msg_type: str = "info"
    priority: Priority = Priority.NORMAL
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    ttl: int = 16
    correlation_id: str = ""     # 关联消息ID（请求-响应）
    
    def to_json(self) -> str:
        return json.dumps({
            "msg_id": self.msg_id, "src_agent": self.src_agent,
            "dst_agent": self.dst_agent, "msg_type": self.msg_type,
            "priority": int(self.priority), "payload": self.payload,
            "timestamp": self.timestamp, "ttl": self.ttl,
            "correlation_id": self.correlation_id,
        }, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, data: str) -> "Message":
        d = json.loads(data)
        d["priority"] = Priority(d["priority"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

# ── 角色资源配额 ──

@dataclass
class ResourceQuota:
    """角色资源配额"""
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    max_concurrent_tasks: int = 10
    rate_limit_per_minute: int = 60
    max_message_queue_size: int = 1000

# ── 完整BaseRole ──

class BaseRole(ABC):
    """Agent角色基类 — 完整状态机实现
    
    生命周期:
    UNINITIALIZED → INITIALIZING → IDLE ⇄ PROCESSING
                                      ↓
                                   DEGRADED → ERROR
                                      ↓
                                 SHUTTING_DOWN → STOPPED
    """
    
    # 子类必须定义
    role_name: str = "Base"
    role_description: str = ""
    permission_level: Permission = Permission.NONE
    allowed_message_types: list[str] = []   # 可处理的消息类型
    heartbeat_interval: float = 5.0
    
    def __init__(self, agent_id: str = None, quota: ResourceQuota = None):
        self.agent_id = agent_id or f"{self.role_name}_{uuid.uuid4().hex[:6]}"
        self.state = RoleState.UNINITIALIZED
        self.quota = quota or ResourceQuota()
        
        # 消息队列
        self._inbox: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=self.quota.max_message_queue_size)
        self._outbox: asyncio.Queue = asyncio.Queue()
        
        # 运行时
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._bus = None
        
        # 统计
        self._stats = {
            "messages_received": 0, "messages_sent": 0,
            "tasks_completed": 0, "tasks_failed": 0,
            "state_changes": 0, "start_time": time.time(),
            "errors": 0,
        }
        
        # 处理器注册表
        self._handlers: dict[str, Callable] = {}
        
        log.info(f"[{self.role_name}] Created: {self.agent_id}")
    
    # ── 状态管理 ──
    
    async def transition_to(self, new_state: RoleState) -> None:
        """状态转换"""
        old_state = self.state
        if old_state == new_state:
            return
        
        # 检查是否合法转换
        valid = self._is_valid_transition(old_state, new_state)
        if not valid:
            log.warning(f"[{self.role_name}] Invalid transition: {old_state.value} → {new_state.value}")
        
        self.state = new_state
        self._stats["state_changes"] += 1
        log.info(f"[{self.role_name}] State: {old_state.value} → {new_state.value}")
        
        # 触发状态变更回调
        await self._on_state_change(old_state, new_state)
    
    def _is_valid_transition(self, old: RoleState, new: RoleState) -> bool:
        """合法状态转换矩阵"""
        valid_transitions = {
            RoleState.UNINITIALIZED: {RoleState.INITIALIZING},
            RoleState.INITIALIZING: {RoleState.IDLE, RoleState.ERROR},
            RoleState.IDLE: {RoleState.PROCESSING, RoleState.WAITING, 
                           RoleState.DEGRADED, RoleState.ERROR, RoleState.SHUTTING_DOWN},
            RoleState.PROCESSING: {RoleState.IDLE, RoleState.WAITING, 
                                 RoleState.DEGRADED, RoleState.ERROR},
            RoleState.WAITING: {RoleState.IDLE, RoleState.PROCESSING, RoleState.ERROR},
            RoleState.DEGRADED: {RoleState.IDLE, RoleState.ERROR, RoleState.SHUTTING_DOWN},
            RoleState.ERROR: {RoleState.IDLE, RoleState.DEGRADED, RoleState.SHUTTING_DOWN},
            RoleState.SHUTTING_DOWN: {RoleState.STOPPED},
        }
        return new in valid_transitions.get(old, set())
    
    async def _on_state_change(self, old: RoleState, new: RoleState) -> None:
        """状态变更钩子"""
        if new == RoleState.DEGRADED:
            log.warning(f"[{self.role_name}] Entering DEGRADED mode — reduced functionality")
        elif new == RoleState.ERROR:
            log.error(f"[{self.role_name}] Entering ERROR state — attempting recovery")
            asyncio.create_task(self._attempt_recovery())
    
    async def _attempt_recovery(self) -> None:
        """错误恢复"""
        await asyncio.sleep(2)
        try:
            if await self.health_check():
                await self.transition_to(RoleState.DEGRADED)
                await self.transition_to(RoleState.IDLE)
                log.info(f"[{self.role_name}] Recovery successful")
        except Exception as e:
            log.error(f"[{self.role_name}] Recovery failed: {e}")
    
    # ── 消息处理 ──
    
    def register_handler(self, msg_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        self._handlers[msg_type] = handler
    
    async def send(self, msg: Message, bus=None) -> None:
        """发送消息"""
        msg.src_agent = self.agent_id
        bus = bus or self._bus
        if bus:
            await bus.publish(msg)
        else:
            await self._outbox.put(msg)
        self._stats["messages_sent"] += 1
    
    async def handle_message(self, msg: Message) -> Optional[Union[Message, list[Message]]]:
        """处理消息 — 子类重写此方法"""
        handler = self._handlers.get(msg.msg_type)
        if handler:
            try:
                return await handler(msg)
            except Exception as e:
                log.error(f"[{self.role_name}] Handler error: {e}")
                self._stats["errors"] += 1
                return Message(
                    src_agent=self.agent_id, dst_agent=msg.src_agent,
                    msg_type="error", priority=Priority.IMPORTANT,
                    payload={"error": str(e), "correlation_id": msg.correlation_id},
                )
        
        # 默认: 返回ACK
        if msg.msg_type == "heartbeat":
            return None
        return Message(
            src_agent=self.agent_id, dst_agent=msg.src_agent,
            msg_type="ack", payload={"received": msg.msg_id},
        )
    
    # ── 生命周期 ──
    
    async def initialize(self) -> bool:
        """初始化角色"""
        await self.transition_to(RoleState.INITIALIZING)
        try:
            success = await self._do_initialize()
            if success:
                await self.transition_to(RoleState.IDLE)
            else:
                await self.transition_to(RoleState.ERROR)
            return success
        except Exception as e:
            log.error(f"[{self.role_name}] Init failed: {e}")
            await self.transition_to(RoleState.ERROR)
            return False
    
    async def _do_initialize(self) -> bool:
        """子类重写的初始化逻辑"""
        return True
    
    async def start(self, message_bus=None) -> None:
        """启动角色主循环"""
        if self.state != RoleState.IDLE:
            raise RuntimeError(f"Cannot start in state: {self.state.value}")
        
        self._bus = message_bus
        self._running = True
        
        # 启动主循环
        main_loop = asyncio.create_task(self._main_loop())
        heartbeat = asyncio.create_task(self._heartbeat_loop())
        
        if message_bus:
            # 如果连接了消息总线，从总线接收消息
            receiver = asyncio.create_task(self._bus_receive_loop(message_bus))
            self._tasks = [main_loop, heartbeat, receiver]
        else:
            self._tasks = [main_loop, heartbeat]
        
        log.info(f"[{self.role_name}] Started: {self.agent_id}")
    
    async def _main_loop(self) -> None:
        """主消息处理循环"""
        while self._running:
            try:
                # 从收件箱取消息
                msg = await asyncio.wait_for(self._inbox.get(), timeout=1.0)
                self._stats["messages_received"] += 1
                
                await self.transition_to(RoleState.PROCESSING)
                
                try:
                    response = await self.handle_message(msg)
                    
                    if response:
                        if isinstance(response, list):
                            for r in response:
                                await self._outbox.put(r)
                        else:
                            await self._outbox.put(response)
                    
                    self._stats["tasks_completed"] += 1
                    
                except Exception as e:
                    log.error(f"[{self.role_name}] Message handling failed: {e}")
                    self._stats["tasks_failed"] += 1
                    self._stats["errors"] += 1
                
                await self.transition_to(RoleState.IDLE)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"[{self.role_name}] Main loop error: {e}")
                await self.transition_to(RoleState.ERROR)
                break
    
    async def _bus_receive_loop(self, bus) -> None:
        """从消息总线接收消息"""
        queue = bus.subscribe(self.agent_id)
        while self._running:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                # 优先级队列入队: (-priority, timestamp, message)
                await self._inbox.put((-int(msg.priority), msg.timestamp, msg))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
    
    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self._running:
            await asyncio.sleep(self.heartbeat_interval)
            if self._bus:
                hb = Message(
                    src_agent=self.agent_id, msg_type="heartbeat",
                    priority=Priority.BACKGROUND,
                    payload={
                        "state": self.state.value,
                        "role": self.role_name,
                        "stats": self._stats,
                    },
                )
                await self._bus.publish(hb)
    
    async def stop(self) -> None:
        """停止角色"""
        await self.transition_to(RoleState.SHUTTING_DOWN)
        self._running = False
        
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        await self.transition_to(RoleState.STOPPED)
        log.info(f"[{self.role_name}] Stopped: {self.agent_id}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        if self.state in (RoleState.ERROR, RoleState.STOPPED):
            return False
        return True
    
    @property
    def stats(self) -> dict:
        return {
            **self._stats,
            "state": self.state.value,
            "agent_id": self.agent_id,
            "role": self.role_name,
            "uptime_s": time.time() - self._stats["start_time"],
        }
    
    def __repr__(self) -> str:
        return f"<{self.role_name}[{self.state.value}] id={self.agent_id}>"

# ── 消息总线 ──

class MessageBus:
    """异步消息总线 — 发布/订阅模式"""
    
    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._max_queue_size = max_queue_size
        self._total_messages = 0
        self._message_log: list[dict] = []
    
    async def publish(self, msg: Message) -> None:
        """发布消息"""
        self._total_messages += 1
        
        # 记录日志
        if len(self._message_log) > 1000:
            self._message_log = self._message_log[-500:]
        self._message_log.append({
            "id": msg.msg_id, "src": msg.src_agent, "dst": msg.dst_agent,
            "type": msg.msg_type, "time": msg.timestamp,
        })
        
        # 路由
        if msg.dst_agent in ("", "*"):
            for queue in self._subscribers.values():
                try:
                    queue.put_nowait(msg)
                except asyncio.QueueFull:
                    pass
        elif msg.dst_agent in self._subscribers:
            try:
                self._subscribers[msg.dst_agent].put_nowait(msg)
            except asyncio.QueueFull:
                pass
    
    def subscribe(self, agent_id: str) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers[agent_id] = queue
        return queue
    
    def unsubscribe(self, agent_id: str) -> None:
        self._subscribers.pop(agent_id, None)
    
    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
    
    @property
    def total_messages(self) -> int:
        return self._total_messages

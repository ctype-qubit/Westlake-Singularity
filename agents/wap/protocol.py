"""WAP — Westlake Agent Protocol
跨Agent联邦通讯协议，灵感来自ActivityPub
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

import json
import time
import uuid
import hashlib
import hmac
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════
# 协议版本
# ═══════════════════════════════════════════
PROTOCOL_VERSION = "0.1.0"
PROTOCOL_NAME = "Westlake Agent Protocol"

class MessageType(str):
    """WAP消息类型"""
    # 感知层
    SENSOR_DATA = "wap.sensor.data"           # 传感器原始数据
    SENSOR_ALERT = "wap.sensor.alert"         # 传感器告警
    
    # 控制层  
    CONTROL_CMD = "wap.control.cmd"           # 控制指令
    CONTROL_RESP = "wap.control.response"     # 控制响应
    TOOL_INVOKE = "wap.tool.invoke"          # 工具调用
    TOOL_RESULT = "wap.tool.result"          # 工具返回
    
    # 认知层
    AGENT_DISCOVERY = "wap.agent.discovery"   # 新发现
    AGENT_HYPOTHESIS = "wap.agent.hypothesis" # 假设
    AGENT_VERIFY = "wap.agent.verify"        # 验证请求
    AGENT_CRITIQUE = "wap.agent.critique"    # 批判性审查
    
    # 联邦层
    FEDERATION_HELLO = "wap.federation.hello" # 跨组握手
    FEDERATION_JOIN = "wap.federation.join"   # 加入联邦
    FEDERATION_LEAVE = "wap.federation.leave" # 离开联邦
    FEDERATION_SYNC = "wap.federation.sync"   # 状态同步
    FEDERATION_DATA = "wap.federation.data"   # 脱敏数据共享
    
    # 系统
    HEARTBEAT = "wap.system.heartbeat"
    ERROR = "wap.system.error"

@dataclass
class WAPMessage:
    """WAP协议标准消息格式"""
    # 必需字段
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    msg_type: str = ""
    src_agent: str = ""           # 发送方Agent ID
    timestamp: float = field(default_factory=time.time)
    protocol_version: str = PROTOCOL_VERSION
    
    # 路由字段
    dst_agent: str = ""           # 接收方 (空=广播)
    dst_lab: str = ""             # 目标实验室 (跨联邦)
    reply_to: str = ""            # 回复消息ID
    
    # 安全字段
    signature: str = ""           # HMAC签名
    encryption: str = "none"      # none | aes256 | tls
    
    # 数据字段
    priority: int = 0             # 0-4 (Background → Critical)
    payload: dict = field(default_factory=dict)
    ttl: int = 16                 # Time-to-live (跳数)
    
    def sign(self, secret: str) -> None:
        """对消息进行HMAC签名"""
        sign_data = f"{self.msg_id}:{self.src_agent}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        self.signature = hmac.new(
            secret.encode(), sign_data.encode(), hashlib.sha256
        ).hexdigest()[:16]
    
    def verify(self, secret: str) -> bool:
        """验证HMAC签名"""
        if not self.signature:
            return False
        sign_data = f"{self.msg_id}:{self.src_agent}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        expected = hmac.new(
            secret.encode(), sign_data.encode(), hashlib.sha256
        ).hexdigest()[:16]
        return hmac.compare_digest(self.signature, expected)
    
    def to_json(self) -> str:
        return json.dumps({
            "msg_id": self.msg_id,
            "msg_type": self.msg_type,
            "src_agent": self.src_agent,
            "dst_agent": self.dst_agent,
            "dst_lab": self.dst_lab,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp,
            "protocol_version": self.protocol_version,
            "signature": self.signature,
            "encryption": self.encryption,
            "priority": self.priority,
            "payload": self.payload,
            "ttl": self.ttl,
        }, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, data: str) -> "WAPMessage":
        d = json.loads(data)
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

# ═══════════════════════════════════════════
# 联邦路由器
# ═══════════════════════════════════════════
class WAPRouter:
    """WAP联邦路由器 — 管理跨组通讯"""
    
    def __init__(self, lab_id: str, lab_name: str, secret: str):
        self.lab_id = lab_id
        self.lab_name = lab_name
        self.secret = secret
        self.peers: dict[str, dict] = {}  # lab_id → {name, url, public_key}
        self.route_table: dict[str, str] = {}  # agent_id → lab_id
        self.local_agents: set[str] = set()
    
    def register_local_agent(self, agent_id: str) -> None:
        """注册本地Agent"""
        self.local_agents.add(agent_id)
        self.route_table[agent_id] = self.lab_id
    
    def add_peer(self, lab_id: str, lab_info: dict) -> None:
        """添加联邦peer实验室"""
        self.peers[lab_id] = lab_info
    
    def route(self, msg: WAPMessage) -> Optional[str]:
        """路由消息：返回目标peer URL或None(本地)"""
        if msg.dst_agent in self.local_agents:
            return None  # 本地消息
        
        if msg.dst_lab and msg.dst_lab in self.peers:
            return self.peers[msg.dst_lab].get("url")
        
        # 广播到所有peers
        return "broadcast"
    
    def discover_agents(self) -> list[dict]:
        """发现所有联邦中的Agent"""
        agents = []
        for agent_id in self.local_agents:
            agents.append({"agent_id": agent_id, "lab_id": self.lab_id, "lab_name": self.lab_name})
        for lab_id, info in self.peers.items():
            for agent in info.get("agents", []):
                agents.append({"agent_id": agent, "lab_id": lab_id, "lab_name": info.get("name", lab_id)})
        return agents

# ═══════════════════════════════════════════
# 联邦握手协议
# ═══════════════════════════════════════════
class FederationHandshake:
    """跨实验室联邦握手"""
    
    @staticmethod
    def create_hello(lab_id: str, lab_name: str, agents: list[str], secret: str) -> WAPMessage:
        msg = WAPMessage(
            msg_type=MessageType.FEDERATION_HELLO,
            src_agent=lab_id,
            payload={
                "lab_name": lab_name,
                "agents": agents,
                "capabilities": ["stm", "dft", "quantum_sim", "data_share"],
            },
        )
        msg.sign(secret)
        return msg
    
    @staticmethod
    def create_join_response(hello_msg: WAPMessage, lab_id: str, secret: str) -> WAPMessage:
        if not hello_msg.verify(secret):
            raise ValueError("Handshake verification failed")
        msg = WAPMessage(
            msg_type=MessageType.FEDERATION_JOIN,
            src_agent=lab_id,
            dst_agent=hello_msg.src_agent,
            reply_to=hello_msg.msg_id,
            payload={"accepted": True, "protocol_version": PROTOCOL_VERSION},
        )
        msg.sign(secret)
        return msg

# ═══════════════════════════════════════════
# 数据脱敏层
# ═══════════════════════════════════════════
class DataAnonymizer:
    """跨组数据共享前的脱敏处理"""
    
    @staticmethod
    def anonymize_stm_data(data: dict) -> dict:
        """脱敏STM数据（去除绝对坐标、校准参数）"""
        safe = dict(data)
        safe.pop("absolute_position_um", None)
        safe.pop("calibration_params", None)
        safe.pop("tip_material", None)
        return safe
    
    @staticmethod
    def anonymize_dft_result(data: dict) -> dict:
        """脱敏DFT结果（保留能带结构，去掉计算参数）"""
        safe = dict(data)
        safe.pop("input_files", None)
        safe.pop("pseudopotentials", None)
        safe.pop("kpoints_exact", None)
        return safe

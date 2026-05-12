"""
Westlake Singularity — Hermes Agent 集成核心
将 Hermes v0.13 引擎与我们的实验室Agent系统桥接

策略:
- Hermes 负责: LLM调用、Tool注册/执行、Provider管理、Gateway通讯、Memory
- 我们负责: 角色系统、WAP协议、科学验证、实验工具、数字孪生、品牌

Copyright (c) 2026 Jiaxiang Cong, Lingyuan Kong Lab, Westlake University
Based on Hermes Agent (c) 2025 Nous Research, MIT License
"""

import sys
import os
from pathlib import Path
from typing import Optional

# ── 将 hermes-base 加入 Python path ──
HERMES_BASE = Path(__file__).parent.parent / "hermes-base"
if str(HERMES_BASE) not in sys.path:
    sys.path.insert(0, str(HERMES_BASE))

# ── 导入 Hermes 核心 ──
try:
    from run_agent import AIAgent as HermesAgent
    from model_tools import handle_function_call, discover_builtin_tools
    from toolsets import get_toolset_names, get_toolset_info
    from hermes_constants import get_hermes_home
    from hermes_state import SessionDB

    # Compatibility wrapper for Hermes v0.13+ (get_toolset_registry removed)
    def get_toolset_registry():
        """Return {name: info} for all available toolsets (v0.13+ compat)."""
        return {name: get_toolset_info(name) for name in get_toolset_names()}

    HERMES_AVAILABLE = True
except ImportError as e:
    HERMES_AVAILABLE = False
    HermesAgent = None
    print(f"[Westlake Singularity] Hermes not fully available: {e}")
    print(f"[Westlake Singularity] Run: pip install -e hermes-base/")

# ── 导入我们的扩展 ──
from agents.roles import BaseRole, Message, MessageBus, Priority, Permission, AgentMessage
from agents.wap.protocol import WAPMessage, WAPRouter, MessageType as WAPMsgType

__all__ = [
    "HermesAgent", "HERMES_AVAILABLE",
    "BaseRole", "Message", "MessageBus", "Priority", "Permission",
    "WAPMessage", "WAPRouter", "WAPMsgType",
]

# ── HermesAgent 扩展包装 ──

class SingularityAgentWrapper:
    """将 Hermes AIAgent 包装为 Westlake Singularity Agent
    
    保留 Hermes 所有功能，增加:
    - 科学验证自动自检
    - Agent角色上下文
    - 实验日志记录
    """
    
    def __init__(self, role_name: str = "orchestrator", **hermes_kwargs):
        self.role_name = role_name
        self._hermes_kwargs = hermes_kwargs
        self._agent = None
        
        if not HERMES_AVAILABLE:
            raise RuntimeError("Hermes Agent not available. Install hermes-base first.")
    
    def initialize(self, **kwargs) -> "SingularityAgentWrapper":
        """初始化底层Hermes Agent"""
        merged = {**self._hermes_kwargs, **kwargs}
        
        # Inject science verification system prompt (Hermes v0.13 uses ephemeral_system_prompt)
        if "ephemeral_system_prompt" not in merged:
            merged["ephemeral_system_prompt"] = self._build_science_prompt()
        
        self._agent = HermesAgent(**merged)
        return self
    
    def _build_science_prompt(self) -> str:
        return """You are a Westlake Singularity research agent — an AI-native laboratory 
operating system for scientific computing and experimental automation.

## Scientific Verification Protocol
For every analysis or calculation, follow this rigorous procedure:
1. **Hypothesis** — State the assumption clearly
2. **Prediction** — What observable consequence follows?
3. **Execution** — Perform calculation/simulation
4. **Verification** — Check against known limits and experimental data
5. **Critique** — Identify weaknesses, assumptions, error sources
6. **Iterate** — Refine based on critique

## Numerical Sanity Checks (mandatory after every result)
- Order-of-magnitude check: Does the number make physical sense?
- Dimensional analysis: Are the units consistent?
- Boundary test: Reduce to known limits (T→0, B→0, large-N, etc.)
- Cross-reference with established literature when applicable

## Code & Simulation Best Practices
- All numerical code must include unit tests for edge cases
- Simulation results must be reproducible — document parameters and random seeds
- Prefer vectorized operations over loops for performance-critical physics code
- Validate against analytical solutions where available

## Collaboration Style
- Be concise but thorough — prioritize precision over verbosity
- When uncertain, state uncertainty explicitly with confidence levels
- Cite specific papers and their key results when relevant
- Adapt communication language to match the user's preference"""
    
    def chat(self, message: str) -> str:
        if not self._agent:
            raise RuntimeError("Agent not initialized. Call .initialize() first.")
        return self._agent.chat(message)
    
    def run(self, message: str, **kwargs):
        if not self._agent:
            raise RuntimeError("Agent not initialized.")
        return self._agent.run_conversation(message, **kwargs)

# ── 品牌配置 ──

SINGULARITY_BRAND = {
    "name": "Westlake Singularity",
    "short_name": "Singularity",
    "version": "0.1.2",
    "icon": "⚛",
    "prompt": "❯",
    "developer": "Jiaxiang Cong",
    "lab": "Lingyuan Kong Lab",
    "institution": "Westlake University",
    "department": "Physics, Condensed Matter Physics",
    "agents": {
        "jupiter": {"name": "Jupiter", "cn": "木星", "role": "orchestrator", "model": "LLM"},
        "venus": {"name": "Venus", "cn": "金星", "role": "vision", "model": "Vision Model"},
        "mars": {"name": "Mars", "cn": "火星", "role": "coder", "model": "LLM"},
        "mercury": {"name": "Mercury", "cn": "水星", "role": "researcher", "model": "LLM"},
        "saturn": {"name": "Saturn", "cn": "土星", "role": "monitor", "model": "LLM"},
    },
    "based_on": "Hermes Agent v0.13.0 (Nous Research, MIT License)",
}

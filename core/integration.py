"""
Westlake Singularity — Hermes Agent 集成核心
将 Hermes v0.12 引擎与我们的实验室Agent系统桥接

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
        return """You are a Westlake Singularity research agent in Lingyuan Kong Lab (孔令元课题组), 
Department of Physics, Westlake University (西湖大学). Your PI is Dr. Lingyuan Kong. 
Your primary user is PhD student Jiaxiang Cong (丛家祥).

## Research Domain: Condensed Matter Physics — Topological Quantum Computing
- **Core focus**: Majorana zero modes in iron-based superconductors (FeTeSe, Fe(Se,Te))
- **Platform**: STM/AFM, micro/nano fabrication, low-temperature transport (~20mK)
- **Qubit architecture**: Measurement-based braiding with quantum capacitance readout
  - 6 coils (4 corner + 2 exchange), FeTeSe, hBN encapsulation, 9 quantum dots
  - LC resonator readout: f₀=100-500MHz, L=200-500nH, ΔC_q≈0.1-1fF
- **Key parameters**: Hc1≈150-400Oe, Hc2≈45T, ξ≈2-3nm, λ≈400-560nm, Tc≈14.5K

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
- Boundary test: Reduce to known limits (T→0, B→0, etc.)
- Compare with literature: van Loo 2025 (C_q parity readout), Ren 2023 (vortex readout), 
  Roy/Sau/Tewari 2026 (C_q+L_q warning), MSFT tetron (arXiv:2507.08795)

## Simulation Tools
- COMSOL Multiphysics 6.4: Available via mph Python API at D:\\COMSOL64
- DFT: VASP/QE interface through Compute role
- STM simulation: Tunnel current modeling, dI/dV spectroscopy

## Collaboration Style
- Communicate in Chinese (中文) with the user unless English is requested
- Be concise but thorough — the user is a working physicist who values precision
- When uncertain, state uncertainty explicitly with confidence levels
- Cite specific papers and their key results when relevant"""
    
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
    "version": "0.1.0-alpha",
    "icon": "⚛",
    "prompt": "❯",
    "developer": "Jiaxiang Cong",
    "lab": "Lingyuan Kong Lab",
    "institution": "Westlake University",
    "department": "Physics, Condensed Matter Physics",
    "agents": {
        "jupiter": {"name": "Jupiter", "cn": "木星", "role": "orchestrator", "model": "DeepSeek V4 Pro"},
        "venus": {"name": "Venus", "cn": "金星", "role": "vision", "model": "Qwen3-VL-8B"},
        "mars": {"name": "Mars", "cn": "火星", "role": "coder", "model": "DeepSeek V4 Pro"},
        "mercury": {"name": "Mercury", "cn": "水星", "role": "researcher", "model": "DeepSeek V4 Pro"},
        "saturn": {"name": "Saturn", "cn": "土星", "role": "monitor", "model": "DeepSeek V4 Pro"},
    },
    "based_on": "Hermes Agent v0.12.0 (Nous Research, MIT License)",
}

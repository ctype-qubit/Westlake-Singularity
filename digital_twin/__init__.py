"""
Westlake Singularity — 数字孪生层
COMSOL桥接 + Sim-to-Real闭环 + DFT对齐
Developer: Westlake Singularity Contributors
"""
from .engine import COMSOLBridge, SimToRealLoop, COMSOLConfig, COMSOLModel, comsol_bridge, sim_real

__all__ = ["COMSOLBridge", "SimToRealLoop", "COMSOLConfig", "COMSOLModel", "comsol_bridge", "sim_real"]

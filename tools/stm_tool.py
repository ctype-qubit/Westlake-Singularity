"""STMTool — Nanonis STM控制工具
模拟STM针尖控制接口，可对接真实Nanonis API
Developer: Westlake Singularity Contributors
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class STMParams:
    """STM扫描参数"""
    bias_V: float = 0.1
    current_pA: float = 100.0
    scan_range_nm: float = 100.0
    pixels: int = 512
    scan_speed_nm_s: float = 100.0
    setpoint_pA: float = 100.0
    z_offset_nm: float = 0.0
    # 高级参数
    pid_p: float = 0.01
    pid_i: float = 0.001
    pid_d: float = 0.0
    lockin_freq_Hz: float = 731.0
    lockin_amplitude_mV: float = 5.0

@dataclass
class STMImage:
    """STM图像数据"""
    data: list  # 2D array
    width_px: int
    height_px: int
    scan_range_nm: float
    bias_V: float
    current_pA: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "width_px": self.width_px,
            "height_px": self.height_px,
            "scan_range_nm": self.scan_range_nm,
            "bias_V": self.bias_V,
            "current_pA": self.current_pA,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

class STMTool:
    """STM控制工具 — Nanonis API风格接口"""
    
    def __init__(self, ip: str = "127.0.0.1", port: int = 6502):
        self.ip = ip
        self.port = port
        self.connected = False
        self.params = STMParams()
        self._position = {"x_um": 0.0, "y_um": 0.0, "z_nm": 0.0}
    
    def connect(self) -> bool:
        """连接到Nanonis控制器（模拟）"""
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        self.connected = False
    
    def set_bias(self, voltage_V: float) -> dict:
        """设置偏压"""
        self.params.bias_V = voltage_V
        return {"status": "ok", "bias_V": voltage_V}
    
    def set_current(self, current_pA: float) -> dict:
        """设置隧穿电流"""
        self.params.current_pA = current_pA
        return {"status": "ok", "current_pA": current_pA}
    
    def set_scan_range(self, range_nm: float) -> dict:
        """设置扫描范围"""
        self.params.scan_range_nm = range_nm
        return {"status": "ok", "scan_range_nm": range_nm}
    
    def tip_approach(self) -> dict:
        """针尖逼近（模拟）"""
        return {"status": "ok", "message": "Tip approached to setpoint"}
    
    def tip_retract(self) -> dict:
        """针尖回退"""
        return {"status": "ok", "message": "Tip retracted"}
    
    def start_scan(self) -> dict:
        """开始扫描（模拟返回结果）"""
        if not self.connected:
            return {"status": "error", "message": "Not connected"}
        return {
            "status": "scanning",
            "params": {
                "bias_V": self.params.bias_V,
                "current_pA": self.params.current_pA,
                "scan_range_nm": self.params.scan_range_nm,
                "pixels": self.params.pixels,
            }
        }
    
    def stop_scan(self) -> dict:
        """停止扫描"""
        return {"status": "stopped"}
    
    def move_tip(self, x_um: float = None, y_um: float = None, z_nm: float = None) -> dict:
        """移动针尖"""
        if x_um is not None:
            self._position["x_um"] = x_um
        if y_um is not None:
            self._position["y_um"] = y_um
        if z_nm is not None:
            self._position["z_nm"] = z_nm
        return {"status": "ok", "position": dict(self._position)}
    
    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "connected": self.connected,
            "position": dict(self._position),
            "params": {
                "bias_V": self.params.bias_V,
                "current_pA": self.params.current_pA,
            }
        }

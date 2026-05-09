"""HardwareTool — 实验室硬件控制抽象层
光源、温控、磁场、真空等
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

from dataclasses import dataclass
from typing import Optional

class HardwareTool:
    """实验室硬件控制"""
    
    def __init__(self):
        self._devices = {}
    
    # ── 温控 ──
    def set_temperature(self, temp_K: float, channel: str = "sample") -> dict:
        return {"status": "ok", "temperature_K": temp_K, "channel": channel}
    
    def get_temperature(self, channel: str = "sample") -> dict:
        return {"temperature_K": 4.2, "channel": channel, "status": "stable"}
    
    # ── 磁场 ──
    def set_magnetic_field(self, field_T: float, axis: str = "z") -> dict:
        max_field = 14.0
        if abs(field_T) > max_field:
            return {"status": "error", "message": f"Field exceeds {max_field}T limit"}
        return {"status": "ok", "field_T": field_T, "axis": axis}
    
    def ramp_field(self, target_T: float, rate_T_min: float = 0.1, axis: str = "z") -> dict:
        return {
            "status": "ramping",
            "target_T": target_T,
            "rate_T_min": rate_T_min,
            "estimated_minutes": abs(target_T) / rate_T_min,
        }
    
    # ── 激光 ──
    def set_laser(self, power_W: float, wavelength_nm: float = 532.0) -> dict:
        if power_W > 1.0:
            return {"status": "error", "message": "Laser power exceeds safety limit"}
        return {"status": "ok", "power_W": power_W, "wavelength_nm": wavelength_nm}
    
    # ── 真空 ──
    def get_vacuum(self) -> dict:
        return {"pressure_mbar": 1e-10, "status": "UHV", "pump_running": True}
    
    # ── 通用 ──
    def emergency_stop(self) -> dict:
        return {"status": "ok", "message": "All systems stopped", "timestamp": None}

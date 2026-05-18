"""HardwareDevices — 硬件设备管理器
AR/VR叠加、灯光、OLED屏幕、激光控制
Developer: Westlake Singularity Contributors
"""

class LightController:
    """实验室氛围灯光控制"""
    
    COLORS = {
        "idle": (10, 22, 40),        # 深蓝 — 待机
        "scanning": (26, 92, 138),   # 西湖蓝 — 扫描中
        "computing": (232, 184, 48), # 量子金 — 计算中
        "discovery": (0, 200, 150),  # 绿 — 有新发现
        "alert": (255, 50, 50),      # 红 — 告警
        "success": (0, 200, 100),    # 绿 — 成功
    }
    
    def __init__(self, device_path: str = "/dev/ttyUSB0"):
        self.device_path = device_path
        self.current_color = "idle"
    
    def set(self, color_name: str) -> dict:
        if color_name in self.COLORS:
            self.current_color = color_name
            r, g, b = self.COLORS[color_name]
            return {"status": "ok", "color": color_name, "rgb": (r, g, b)}
        return {"status": "error", "message": f"Unknown color: {color_name}"}
    
    def pulse_discovery(self) -> dict:
        """发现脉冲效果（金色闪烁）"""
        return {"status": "ok", "effect": "pulse", "color": "discovery"}


class OLEDDisplay:
    """OLED信息屏"""
    
    def __init__(self, i2c_address: int = 0x3C):
        self.i2c_address = i2c_address
        self.current_text: list[str] = []
    
    def show(self, lines: list[str]) -> dict:
        self.current_text = lines
        return {"status": "ok", "lines": lines}
    
    def show_status(self, agent_count: int, task: str, temp_K: float) -> dict:
        return self.show([
            f"Agents: {agent_count} active",
            f"Task: {task[:20]}",
            f"Temp: {temp_K:.1f} K",
        ])
    
    def show_alert(self, message: str) -> dict:
        return self.show([f"⚠ ALERT ⚠", message[:20]])


class ARHUD:
    """AR/VR抬头显示叠加"""
    
    def __init__(self):
        self.overlays: list[dict] = []
    
    def add_overlay(self, text: str, position: tuple, color: str = "#e8b830") -> dict:
        overlay = {"text": text, "position": position, "color": color}
        self.overlays.append(overlay)
        return {"status": "ok", "overlay": overlay}
    
    def clear(self) -> dict:
        self.overlays.clear()
        return {"status": "ok"}
    
    def highlight_region(self, x: float, y: float, w: float, h: float, 
                         label: str = "") -> dict:
        return self.add_overlay(
            f"{label} [{x:.1f},{y:.1f}]", 
            (x + w/2, y - 10),
            "#00c896"
        )

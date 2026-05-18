"""
Westlake Singularity — COMSOL Multiphysics桥接器
Developer: Westlake Singularity Contributors
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger("singularity.dt")

@dataclass
class COMSOLConfig:
    comsol_root: str = r"D:\COMSOL64"
    python_exe: str = r"C:\Users\Admin\PyCharmMiscProject\.venv\Scripts\python.exe"
    scripts_dir: str = r"C:\Users\Admin\hermes_comsol"

@dataclass
class COMSOLModel:
    name: str
    mph_file: str
    params: dict = field(default_factory=dict)
    study: str = "std1"
    last_result: Optional[dict] = None
    last_solve_time: float = 0.0

class COMSOLBridge:
    def __init__(self, config: COMSOLConfig = None):
        self.config = config or COMSOLConfig()
        self._models: dict = {}
        self._comsol_available = Path(self.config.comsol_root).exists()

    def _build_solve_script(self, model: COMSOLModel, cores: int = 4) -> str:
        """构建COMSOL求解脚本 — 使用字符串拼接避免f-string转义"""
        params_json = json.dumps(model.params)
        
        script = (
            '"""COMSOL Solve Script - Westlake Singularity"""\n'
            'import mph, json, sys, traceback\n'
            'try:\n'
            '    client = mph.start(cores=' + str(cores) + ')\n'
            '    model = client.load(r"' + model.mph_file.replace('\\', '\\\\') + '")\n'
            '    params = ' + params_json + '\n'
            '    for name, value in params.items():\n'
            '        model.parameter(name, str(value))\n'
            '    model.mesh("mesh1").run()\n'
            '    model.solve("' + model.study + '")\n'
            '    results = {}\n'
            '    try:\n'
            '        results["magnetic_field_T"] = model.evaluate(["mf.normB"], unit="T")\n'
            '    except: pass\n'
            '    try:\n'
            '        results["temperature_K"] = model.evaluate(["ht.T"], unit="K")\n'
            '    except: pass\n'
            '    model.save()\n'
            '    print(json.dumps({"status":"ok","results":results}))\n'
            'except Exception as e:\n'
            '    print(json.dumps({"status":"error","message":str(e)}))\n'
            'finally:\n'
            '    try: client.remove(model)\n'
            '    except: pass\n'
        )
        return script

    def _build_param_script(self, model: COMSOLModel) -> str:
        return (
            'import mph, json\n'
            'try:\n'
            '    client = mph.start()\n'
            '    model = client.load(r"' + model.mph_file.replace('\\', '\\\\') + '")\n'
            '    params = {}\n'
            '    for name in model.parameters():\n'
            '        params[name] = model.parameter(name)\n'
            '    print(json.dumps({"status":"ok","parameters":params}))\n'
            'except Exception as e:\n'
            '    print(json.dumps({"status":"error","message":str(e)}))\n'
        )

    def _execute_on_windows(self, script: str, timeout: int = 600) -> dict:
        script_path = Path(self.config.scripts_dir) / f"comsol_{int(time.time())}.py"
        script_path.write_text(script, encoding="utf-8")
        win_path = str(script_path).replace("/mnt/c/", "C:\\").replace("/", "\\")
        
        try:
            result = subprocess.run(
                [self.config.python_exe, win_path],
                capture_output=True, text=True, timeout=timeout,
                cwd=self.config.scripts_dir
            )
            script_path.unlink(missing_ok=True)
            for line in result.stdout.strip().split("\n"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
            return {"status": "ok", "raw_output": result.stdout}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Timeout ({timeout}s)"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def solve(self, model_name: str, cores: int = 4, timeout: int = 600) -> dict:
        if model_name not in self._models:
            return {"status": "error", "message": f"Model not found: {model_name}"}
        model = self._models[model_name]
        
        if self._comsol_available:
            script = self._build_solve_script(model, cores)
            result = self._execute_on_windows(script, timeout)
            if result.get("status") == "ok" and "results" in result:
                model.last_result = result["results"]
                model.last_solve_time = time.time()
            return result
        else:
            import random
            return {
                "status": "simulated",
                "warning": "COMSOL unavailable — simulated results",
                "results": {
                    "magnetic_field_T": round(random.uniform(0.1, 13.5), 3),
                    "temperature_K": round(random.uniform(0.02, 4.2), 3),
                    "mesh_elements": random.randint(10000, 100000),
                }
            }

    def load_model(self, name: str, mph_path: str, params: dict = None) -> dict:
        self._models[name] = COMSOLModel(name=name, mph_file=mph_path, params=params or {})
        return {"status": "ok", "model": name}

    def set_parameter(self, model_name: str, param_name: str, value: float) -> dict:
        if model_name not in self._models:
            return {"status": "error", "message": f"Model not found: {model_name}"}
        self._models[model_name].params[param_name] = value
        return {"status": "ok", "param": param_name, "value": value}

    def param_sweep(self, model_name: str, param_name: str,
                    start: float, stop: float, n_points: int) -> dict:
        import numpy as np
        values = np.linspace(start, stop, n_points)
        results = []
        for val in values:
            self.set_parameter(model_name, param_name, float(val))
            result = self.solve(model_name)
            results.append({"param_value": float(val), "result": result})
        return {"status": "ok", "param": param_name, "range": [start, stop], "n_points": n_points, "results": results}

    def list_models(self) -> list:
        return list(self._models.keys())

@dataclass
class SimRealConfig:
    tolerance: float = 0.05
    max_iterations: int = 10
    convergence_window: int = 3
    parameter_bounds: dict = field(default_factory=dict)

class SimToRealLoop:
    def __init__(self, comsol: COMSOLBridge, stm_controller=None, config: SimRealConfig = None):
        self.comsol = comsol
        self.stm = stm_controller
        self.config = config or SimRealConfig()
        self._history = []
        self._convergence_count = 0

    async def optimize(self, model_name: str, target_param: str, experiment_func) -> dict:
        history = []
        for i in range(self.config.max_iterations):
            sim_result = self.comsol.solve(model_name)
            sim_value = sim_result.get("results", {}).get(target_param)
            if sim_value is None:
                return {"status": "error", "message": f"No {target_param} in sim results"}
            try:
                exp_result = await experiment_func(self.comsol._models[model_name].params)
                exp_value = exp_result.get(target_param)
            except Exception as e:
                return {"status": "error", "message": f"Experiment failed: {e}"}
            
            deviation = abs(sim_value - exp_value) / max(abs(exp_value), 1e-10)
            history.append({"iteration": i+1, "sim_value": sim_value, "exp_value": exp_value, "deviation": deviation})
            
            if deviation < self.config.tolerance:
                self._convergence_count += 1
                if self._convergence_count >= self.config.convergence_window:
                    return {"status": "converged", "iterations": i+1, "final_deviation": deviation, "history": history}
            else:
                self._convergence_count = 0
                scale = exp_value / sim_value if sim_value != 0 else 1.0
                for pname in self.config.parameter_bounds:
                    current = self.comsol._models[model_name].params.get(pname, 0)
                    self.comsol.set_parameter(model_name, pname, current * (1 + (scale - 1) * 0.5))
        return {"status": "max_iterations", "iterations": self.config.max_iterations, "history": history}

comsol_bridge = COMSOLBridge()
sim_real = SimToRealLoop(comsol_bridge)

---
name: comsol-setup
description: COMSOL Multiphysics 6.4 configuration for Hermes Agent — mph integration, WSL/Windows bridge, GitHub resources, and simulation workflow.
---

## 环境概览

- **COMSOL 版本**: 6.4.0.293
- **安装位置**: `D:\COMSOL64\Multiphysics` (Windows)
- **WSL 路径**: `/mnt/d/COMSOL64/Multiphysics`
- **许可模块**: 47 个（AC/DC, RF, Semiconductor, Structural Mechanics, Wave Optics, etc.）
- **mph 版本**: 1.3.1（已安装在 Windows Python 和 WSL Python）
- **Windows Python**: `C:\Users\Admin\PyCharmMiscProject\.venv\Scripts\python.exe`
- **WSL Python**: `/usr/local/lib/hermes-agent/venv/bin/python3`
- **Linux JVM**: OpenJDK 21 at `/usr/lib/jvm/java-21-openjdk-amd64/lib/server/libjvm.so`

## 关键限制

mph Client-Server 模式在 WSL 上无法直接连接 Windows COMSOL 服务器，因为 `ModelUtil.connect()` 需要 Windows 认证（NTLM/Kerberos），WSL 中没有。

**解决方案：通过 MCP Server 调用** — COMSOL MCP Server 运行在 Windows Python 上，Hermes 通过 MCP stdio 协议与之通信。MCP Server 内部使用 `mph.Client()` stand-alone 模式（Windows 原生认证）。

## MCP Server 配置

已配置在 `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  comsol:
    command: /mnt/c/Users/Admin/PyCharmMiscProject/.venv/Scripts/python.exe
    args: ["C:\\Users\\Admin\\hermes_comsol\\comsol_mcp_launcher.py"]
    timeout: 600
    connect_timeout: 120
```

重启 Hermes Agent 后生效。可用的 MCP 工具包括:
- `mcp_comsol_comsol_start` — 启动 COMSOL 会话
- `mcp_comsol_comsol_create_model` — 创建模型
- `mcp_comsol_comsol_add_block` — 添加几何体
- `mcp_comsol_comsol_set_physics` — 设置物理场
- `mcp_comsol_comsol_mesh` — 网格划分
- `mcp_comsol_comsol_solve` — 求解
- `mcp_comsol_comsol_evaluate` — 结果评估
- 等等...

```bash
/mnt/c/Users/Admin/PyCharmMiscProject/.venv/Scripts/python.exe "C:\Users\Admin\hermes_comsol\your_script.py"
```

## 脚本模板

```python
import mph
client = mph.start()
model = client.create('model_name')
# ... geometry, physics, mesh, solve ...
model.save(r'C:\Users\Admin\hermes_comsol\model.mph')
client.remove(model)
```

## GitHub 仓库列表

位于 `C:\Users\Admin\hermes_comsol\github\`（12个仓库，共1.2GB）:

| 仓库 | 用途 |
|------|------|
| COMSOL_Multiphysics_MCP | MCP Server - AI Agent 控制 COMSOL |
| SQDMetal | 超导量子器件仿真+微纳加工 |
| nanoEM | MIT 纳米尺度电磁学 |
| comsol-mcp-gui | GUI MCP (Java Shell) |
| universal-scientific-comsol-agent | 完整科学Agent工作台 |
| LLM-COMSOL-Piezo-PEH-Agent | LLM驱动参数优化 |
| AI-mag | ETH FEM+ANN 电感优化 |
| cmphy | mph替代品 |
| bem-comsol | BEM静电场+离子阱 |
| comsol-mcp-physics | 物理感知MCP |
| comsol-mph-analyzer | mph模型分析器 |
| Comsol-Workflow | mph工作流示例 |

## 已验证

电容测试仿真（geometry → physics → mesh → solve → save）已通过。
模型: `C:\Users\Admin\hermes_comsol\capacitor_test.mph`

## 常见问题

- "No user name and password could be obtained" → 用 Windows Python 而非 WSL Python
- study.create 参数错误 → 用 Java API: `model.java.study().create("name")` + `std.run()`
- "No studies defined" → 先创建 study 再 solve

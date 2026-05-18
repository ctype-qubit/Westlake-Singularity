# 🤖 Team · 西湖奇点 Agent 团队

> "实验室即科学家" — 每个 Agent 都是课题组的一员

---

## 科学验证方法论

每次分析或计算，严格遵循:

1. **假设** — 清晰陈述前提条件
2. **预测** — 可观测的推论是什么？
3. **执行** — 完成计算/模拟
4. **验证** — 对照已知极限和实验数据
5. **批判** — 识别弱点、假设、误差源
6. **迭代** — 基于批判进行改进

**数值自查（每次结果后必做）**:
- 量级检查: 数字在物理上合理吗？
- 量纲分析: 单位一致吗？
- 边界测试: 还原到已知极限
- 文献对照: 交叉验证已有成果

## 模拟工具栈

| 工具 | 用途 | 接口 |
|------|------|------|
| COMSOL 6.4 | 多物理场仿真 | mph Python API |
| VASP/QE | DFT第一性原理 | Compute Role |
| KLayout/GDSPY | 微纳加工版图 | Layout Design skill |
| vLLM | LLM推理服务 | Compute Role |

---

## 团队架构

```
                    ⚛ Jupiter (木星)
                  中控 · 论文撰写 · 对外接口
                   ╱    │    │    │    ╲
                  ╱     │    │    │     ╲
          🖼️ Venus  🔬 Mars  📚 Mercury  🛰️ Saturn
          (金星)    (火星)    (水星)      (土星)
         视觉/PPT  代码审查  深度研究    文献监控
            │         │        │           │
         Qwen3VL   V4 Pro   V4 Pro      V4 Pro
         (本地)   (DeepSeek)(DeepSeek)  (DeepSeek)
```

---

## 核心成员

| Agent | 代号 | 模型 | 职责 |
|-------|------|------|------|
| **Jupiter** | 木星 | DeepSeek V4 Pro | 中央控制、论文撰写、跨Agent调度、用户对话 |
| **Venus** | 金星 | Qwen3-VL-8B (本地) | 视觉分析、数据可视化、PPT制作、LaTeX排版 |
| **Mars** | 火星 | DeepSeek V4 Pro | 代码审查、算法实现、工具开发、debugging |
| **Mercury** | 水星 | DeepSeek V4 Pro | 深度科研、文献解读、实验设计、假设生成 |
| **Saturn** | 土星 | DeepSeek V4 Pro | 文献监控 (arXiv+blogwatch)、组会报告准备 |

---

## Agent 角色系统 (v0.2.0)

| 角色 | 等级 | 职责 |
|------|------|------|
| 🛡️ **Guard** | LV5 | 传感器安全监控、阈值报警、紧急停机 |
| 🗺️ **Mapper** | LV3 | STM扫描专家、图像质量评估、漂移矫正 |
| 🔍 **Discovery** | LV4 | 异常发现、相变检测、拓扑信号识别 |
| 🧭 **Orchestrator** | LV5 | 中央控制、任务DAG分解、资源仲裁 |
| 💻 **Compute** | LV2 | 超算调度、Slurm管理、vLLM推理、DFT计算 |

---

## 扩展角色（未来）

| 代号 | 职责 |
|------|------|
| **Neptune** 海王星 | 超算调度专精 (Slurm/vLLM管理) |
| **Pluto** 冥王星 | 数据持久化 + 向量数据库管理 |
| **Gaia** 盖亚 | 数字孪生引擎 (COMSOL/DFT实时对齐) |
| **Athena** 雅典娜 | 实验安全守护 (传感器阈值+异常报警) |
| **Prometheus** 普罗米修斯 | 联邦学习 + 跨组知识迁移 |

---

## 开发者签名

```
Westlake Singularity v0.2.0
Developer: Westlake Singularity Team
Lab: Westlake University
Institution: Westlake University (西湖大学)
Department: Physics, Condensed Matter Physics
Location: Hangzhou, China

AI Team: Jupiter · Venus · Mars · Mercury · Saturn
Built on: Hermes Agent v0.13.0 (Nous Research · MIT License)
```

---

*"千帆竞发，百舸争流"* — 西湖大学 · 凝聚态物理

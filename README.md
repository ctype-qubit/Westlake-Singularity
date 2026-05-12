# ⚛ AI-Native Quantum Laboratory Operating System

<p align="center">
 
</p>

<p align="center">
  <strong>AI-Native Quantum Laboratory Operating System</strong><br>

</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-0.1.2-blue.svg" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python"></a>
</p>

---


## 🤖 Agent 角色系统

| 角色 | 等级 | 职责 |
|------|------|------|
| 🛡️ **Guard** | LV5 | 传感器专用 |
| 🗺️ **Mapper** | LV3 | 设备专家 |
| 🔍 **Discovery** | LV4 | 自检及任务输出检查 |
| 🧭 **Orchestrator** | LV5 | 中央控制：任务DAG分解、资源仲裁、实验序列编排 |
| 💻 **Compute** | LV2 | 超算调度：Slurm作业管理、vLLM推理、DFT计算对齐 |

 各Agent 通过 **WAP** 实时通讯，形成蜂群智能。

---

## 🚀 一行安装

```bash
git clone https://github.com/ctype-qubit/Westlake-Singularity.git && cd Westlake-Singularity && bash install.sh
```

> 需要 Python 3.11+，macOS: `brew install python@3.11`

## 🖥️ 启动

```bash
singularity --version          # 查看版本和团队签名
singularity --banner           # 显示像素风 Banner
singularity --status           # 系统状态
singularity --role all         # 启动全部5个Agent角色
singularity --role orchestrator --single  # 单Agent对话模式
```

---

## 🔧 硬件需求

| 层级 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 单Agent开发 | 8GB RAM, 4核 | 16GB RAM, 8核 |
| 多Agent蜂群 | 32GB RAM, 16核 | 64GB RAM, 32核 + GPU |
| 实验室全栈 | 128GB RAM, 32核, A100 | 256GB RAM, 64核, 4×A100 |
| 超算节点 | 连接Slurm集群 | InfiniBand互联 |

---

## 📂 项目结构

```
westlake-singularity/
├── core/           # 核心框架 (fork自Hermes Agent)
├── agents/         # Agent系统
│   ├── roles/      # 角色定义
│   ├── protocols/  # 通讯协议
│   └── wap/        # 安全协议
├── perception/     # 感知层 (vision/audio/LiDAR)
├── tools/          # 工具层 
├── compute/        # 超算集成 (Slurm/vLLM)
├── memory/         # 记忆宫殿 (向量DB/RAG)
├── bus/            # 事件总线 (WebSocket/设备)
├── branding/       # 品牌资产 (像素Logo/配色)
└── docs/           # 文档
```

---

## 👥 团队

| 角色 | 姓名 | 单位 |
|------|------|------|
| 🎓 博士生 | **丛家祥** (Jiaxiang Cong) | 西湖大学 · 物理系 |
| 👨‍🏫 PI | **孔令元** 博士 | 西湖大学 · 物理系 |
| 🤖 AI Partner | **Jupiter** (木星) | Lab Agent |

---

## 📄 许可证

本项目基于 MIT 协议开源。基于 Nous Research 的 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 框架（MIT License）。

```
MIT License · Copyright (c) 2026 Jiaxiang Cong · Westlake University
```

---

*"The laboratory itself becomes the scientist."* — 丛家祥, 2026

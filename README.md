# ⚛ Westlake Singularity · 西湖奇点

<p align="center">
  <img src="branding/pixel_art/shield_32x32.txt" alt="Westlake Singularity" width="200">
</p>

<p align="center">
  <strong>AI-Native Quantum Laboratory Operating System</strong><br>
  <em>西湖大学 · AI量子实验室操作系统</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/version-0.1.0--alpha-gold.svg" alt="Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python"></a>
</p>

---

## 🎯 愿景

> **我们建造的不是一个Agent，而是一整个 AI-Native 的量子实验室。**

Westlake Singularity 是西湖大学孔令元团队打造的 **AI原生量子实验室操作系统**。它基于开源 Hermes Agent 框架深度重构，将千个共生 AI Agent 编织成一个科学发现蜂群——从 STM 针尖的扫描优化到 DFT 计算的对齐验证，从实验数据的异常发现到论文的自动撰写，全流程 AI 自主闭环。

---

## 🏗️ 六层架构

```
┌─────────────────────────────────────────┐
│  🏛️ 层6 · 联邦帝国    ← 跨组WAP协议     │
│     多实验室Agent联邦，科研外交协议       │
├─────────────────────────────────────────┤
│  🪞 层5 · 数字孪生    ← Sim-to-Real      │
│     COMSOL/DFT虚拟 → STM实体验证        │
├─────────────────────────────────────────┤
│  🧠 层4 · 认知层      ← 推理+验证循环    │
│     Guard守护/Mapper映射/Discovery发现   │
├─────────────────────────────────────────┤
│  🎮 层3 · 控制层      ← gRPC/WebSocket   │
│     Nanonis API, 超算Slurm, 硬件控制     │
├─────────────────────────────────────────┤
│  📡 层2 · 感知层      ← 8K视觉+LiDAR     │
│     多模态传感器, 实时流式数据           │
├─────────────────────────────────────────┤
│  ⚛️  层1 · 物理层      ← 量子比特        │
│     FeTeSe+hBN+QD, Majorana编织         │
└─────────────────────────────────────────┘
```

---

## 🤖 Agent 角色系统

| 角色 | 等级 | 职责 |
|------|------|------|
| 🛡️ **Guard** | LV5 | 安全守护：传感器阈值监控、实验室异常报警、心跳检测 |
| 🗺️ **Mapper** | LV3 | STM成像专家：扫描参数优化、图像质量评分、漂移矫正 |
| 🔍 **Discovery** | LV4 | 异常猎手：相变检测、拓扑信号识别、patch-clamp触发 |
| 🧭 **Orchestrator** | LV5 | 中央控制：任务DAG分解、资源仲裁、实验序列编排 |
| 💻 **Compute** | LV2 | 超算调度：Slurm作业管理、vLLM推理、DFT计算对齐 |

千个 Agent 通过 **WAP (Westlake Agent Protocol)** 实时通讯，形成蜂群智能。

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
│   └── wap/        # Westlake Agent Protocol
├── perception/     # 感知层 (vision/audio/LiDAR)
├── tools/          # 工具层 (STM/DFT/硬件)
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
| 👨‍🏫 PI | **孔令元** 博士 | 西湖大学 · 凝聚态物理 |
| 🤖 AI Partner | **Jupiter** (木星) | Westlake Singularity 中控Agent |

---

## 📄 许可证

本项目基于 MIT 协议开源。基于 Nous Research 的 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 框架（MIT License）。

```
MIT License · Copyright (c) 2026 Jiaxiang Cong · Westlake University
```

---

*"The laboratory itself becomes the scientist."* — 丛家祥, 2026

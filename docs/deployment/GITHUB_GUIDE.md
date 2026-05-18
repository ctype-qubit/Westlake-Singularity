# 🚀 GitHub 上传指南

## 开发者: Westlake Singularity · Westlake University

---

## 第一步：在 GitHub 创建仓库

1. 打开 https://github.com/new
2. Repository name: `westlake-singularity`
3. Description: `⚛ AI-Native Quantum Laboratory OS — 西湖大学AI量子实验室`
4. Public ✅ (MIT开源)
5. **不要**勾选 "Add a README file"（我们已有）
6. 点击 "Create repository"

---

## 第二步：初始化 Git 并推送

```bash
# 进入项目目录
cd F:/westlake-singularity

# 初始化 Git
git init
git add .
git commit -m "🎉 Initial commit: Westlake Singularity v0.2.0-alpha

Developer: Westlake Singularity Contributors
Team: Jupiter · Venus · Mars · Mercury · Saturn

- Six-layer architecture (Perception→Control→Cognition→Federation→Digital Twin→Empire)
- Five agent roles (Guard, Mapper, Discovery, Orchestrator, Compute)
- WAP (Westlake Agent Protocol) for cross-lab federation
- Realtime tools (STM/Nanonis, DFT, WebSocket streaming)
- Pixel art branding with Westlake University colors
- Docker Compose multi-agent deployment"

# 连接远程仓库
git remote add origin https://github.com/jiaxiang-cong/westlake-singularity.git

# 推送
git branch -M main
git push -u origin main
```

---

## 第三步：其他用户一键下载

```bash
# 方式1: git clone
git clone https://github.com/jiaxiang-cong/westlake-singularity.git
cd westlake-singularity
pip install -e .

# 方式2: pip 直接安装
pip install git+https://github.com/jiaxiang-cong/westlake-singularity.git

# 方式3: Docker 一键启动
git clone https://github.com/jiaxiang-cong/westlake-singularity.git
cd westlake-singularity
docker compose -f docker/docker-compose.yml up -d
```

---

## 第四步：发布 Release

1. 在 GitHub 仓库页面点击 "Releases" → "Create a new release"
2. Tag: `v0.2.0-alpha`
3. Title: `Westlake Singularity v0.2.0-alpha — 西湖奇点初版`
4. 描述内容建议：

```
## ⚛ Westlake Singularity v0.2.0-alpha

首个公开版本。包含完整的六层架构骨架和五个Agent角色系统。

### 新特性
- 🏗️ 六层架构 (感知→控制→认知→联邦→数字孪生→帝国)
- 🤖 五个Agent角色 (Guard, Mapper, Discovery, Orchestrator, Compute)
- 📡 WAP跨实验室联邦协议
- 🔧 STM/Nanonis + DFT + WebSocket 工具层
- 🎨 西湖大学像素Logo + 终端配色方案
- 🐳 Docker Compose 多Agent一键部署

### 开发者
Westlake Singularity · Westlake University
AI Team: Jupiter (木星) · Venus (金星) · Mars (火星) · Mercury (水星) · Saturn (土星)
```

---

## 日常更新工作流

```bash
git add .
git commit -m "描述你的改动"
git push

# 或者用GitHub Desktop (Windows图形界面)
# 打开 GitHub Desktop → Add existing repository → 选 F:/westlake-singularity
```

---

*记得先配置好 Git 用户名：*
```bash
git config --global user.name "Westlake Singularity User"
git config --global user.email "singularity@westlake.edu.cn"
```

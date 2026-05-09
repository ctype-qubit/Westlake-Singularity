#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║  ⚛  WESTLAKE SINGULARITY — 一键安装脚本                ║
# ║  Developer: Jiaxiang Cong · Lingyuan Kong Lab            ║
# ║  Westlake University · Physics · CMP                      ║
# ║  Team: Jupiter(木星) Venus(金星) Mars(火星)               ║
# ║        Mercury(水星) Saturn(土星)                         ║
# ╚══════════════════════════════════════════════════════════╝
set -e

BOLD="\033[1m"
GREEN="\033[32m"
GOLD="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║  ⚛  WESTLAKE SINGULARITY            ║"
echo "║  AI-Native Quantum Laboratory OS     ║"
echo "╚══════════════════════════════════════╝"
echo -e "${RESET}"

# Python check
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found. Install: brew install python@3.11"
    exit 1
fi

PY=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${RESET} Python $PY"

# Install Singularity
echo -e "${GOLD}→${RESET} Installing Westlake Singularity..."
pip install -e . -q 2>&1 | tail -1

# Install Hermes Agent base
echo -e "${GOLD}→${RESET} Installing Hermes Agent base..."
pip install -e hermes-base -q 2>&1 | tail -1

# Verify
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
singularity --version 2>/dev/null || python3 cli.py --version
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "  ${BOLD}Done!${RESET}  Run: ${CYAN}singularity --help${RESET}"
echo ""

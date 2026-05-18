#!/usr/bin/env python3
"""Westlake Singularity — ASCII启动Banner生成器
用法: python banner.py  或  python banner.py --big
"""

import sys
import shutil

# ── 配色方案 ──────────────────────────────────────────
class Colors:
    """西湖奇点配色：深蓝底 + 量子金"""
    DEEP_BLUE   = '\033[48;2;10;22;40m'   # #0a1628
    GOLD        = '\033[38;2;232;184;48m'   # #e8b830
    WESTLAKE_BLUE = '\033[38;2;26;92;138m'  # #1a5c8a
    WHITE       = '\033[38;2;240;240;240m'  # #f0f0f0
    CYAN        = '\033[38;2;0;200;200m'
    RESET       = '\033[0m'
    BOLD        = '\033[1m'
    DIM         = '\033[2m'

# ── 像素Logo：西湖大学盾牌 + 量子比特 ──────────────────
PIXEL_LOGO = r"""
{dim}╔══════════════════════════════════════╗
║  {gold}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{dim}  ║
║  {gold}▓▓{blue}╔══╗{gold}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{dim}  ║
║  {gold}▓▓{blue}║{white}⚛{blue} ║{gold}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{dim}  ║
║  {gold}▓▓{blue}╚══╝{gold}▓▓▓▓{blue}╔══════╗{gold}▓▓▓▓▓▓▓▓▓▓▓{dim}  ║
║  {gold}▓▓▓▓▓▓▓▓▓▓{blue}║ {white}W E S T L A K E{blue} ║{dim}  ║
║  {gold}▓▓▓▓▓▓▓▓▓▓{blue}║ {white}S I N G U L A R I T Y{blue} ║{dim}  ║
║  {gold}▓▓▓▓▓▓▓▓▓▓{blue}╚══════╝{gold}▓▓▓▓▓▓▓▓▓▓▓{dim}  ║
║  {gold}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{dim}  ║
║  {gold}▓▓{blue}╔══╗{gold}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{blue}╔══╗{gold}▓▓▓▓▓{dim}  ║
║  {gold}▓▓{blue}║{white}|0⟩{blue}║{gold}▓▓▓▓▓▓▓▓▓▓▓{blue}║{white}|1⟩{blue}║{gold}▓▓▓▓▓{dim}  ║
║  {gold}▓▓{blue}╚══╝{gold}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{blue}╚══╝{gold}▓▓▓▓▓{dim}  ║
║  {gold}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{dim}  ║
╚══════════════════════════════════════╝{reset}""".format(
    dim=Colors.DIM, gold=Colors.GOLD, blue=Colors.WESTLAKE_BLUE,
    white=Colors.WHITE, reset=Colors.RESET
)

# ── ASCII Banner ─────────────────────────────────────
BANNER_SMALL = r"""
{cyan}   ▄     ▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄     ▄
{cyan}   ▐ ▌   ▐ ▐      ▐       ▐       ▐ ▌   ▐ 
{cyan}   ▐▛▀▀▀▀▌▐▛▀▀▀▀▌▐▛▀▀▀▀▌▐▛▀▀▀▀▌▐▛▀▀▀▀▌
{gold}   ▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐
{gold}   ▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐
{gold}   ▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐  {white}西湖奇点™
{gold}   ▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐
{gold}   ▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐  {dim}Westlake Singularity
{gold}   ▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐
{gold}   ▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐▐▌   ▐  {dim}v0.2.0 — AI-Native Quantum Lab
{gold}    ▀     ▀     ▀     ▀     ▀     ▀{reset}
""".format(
    cyan=Colors.CYAN, gold=Colors.GOLD, white=Colors.WHITE,
    dim=Colors.DIM, reset=Colors.RESET
)

BANNER_BIG = r"""
{cyan}╦ ╦┌─┐┌─┐┌┬┐┬  ┌─┐┬┌─┌─┐  ╔═╗┬┌┐┌┌─┐┬ ┬┬  ┌─┐┬─┐┬┌┬┐┬ ┬
║║║├┤ └─┐ │ │  ├─┤├┴┐├┤   ╚═╗│││││ ┬│ ││  ├─┤├┬┘│ │ └┬┘
╚╩╝└─┘└─┘ ┴ ┴─┘┴ ┴┴ ┴└─┘  ╚═╝┴┘└┘└─┘└─┘┴─┘┴ ┴┴└─┴ ┴ ┴ 
{gold}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {white}AI-Native Quantum Laboratory Operating System
  {dim}西湖大学 · Westlake University
    {dim}Developer: Westlake Singularity Contributors
    Agents: Jupiter(木星) Venus(金星) Mars(火星) Mercury(水星) Saturn(土星)
    MIT License · v0.2.0-alpha · Build 2026
{reset}""".format(
    cyan=Colors.CYAN, gold=Colors.GOLD, white=Colors.WHITE,
    dim=Colors.DIM, reset=Colors.RESET
)


def show_banner(big=False):
    """显示启动Banner"""
    print(Colors.DEEP_BLUE + "\n" * 3, end="")
    print(PIXEL_LOGO)
    print()
    print(BANNER_BIG if big else BANNER_SMALL)
    print(Colors.DEEP_BLUE)

def show_minimal():
    """精简版（用于CLI启动）"""
    print(f"{Colors.CYAN}{Colors.BOLD}⚛ Westlake Singularity{Colors.RESET} {Colors.DIM}v0.2.0{Colors.RESET}")
    print(f"{Colors.DIM}  西湖大学 AI量子实验室操作系统{Colors.RESET}")


if __name__ == "__main__":
    big = "--big" in sys.argv or "-b" in sys.argv
    try:
        show_banner(big)
    except KeyboardInterrupt:
        print(Colors.RESET)

"""
Westlake Singularity CLI — 完整命令行界面
基于 Hermes CLI 重构，使用 Westlake Singularity 品牌
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

# 将项目根目录加入Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "hermes-base"))

def show_banner():
    """显示启动Banner"""
    try:
        from branding.banner import show_banner
        show_banner(big=True)
    except ImportError:
        print(r"""
╔══════════════════════════════════════════════════════╗
║  ⚛  WESTLAKE SINGULARITY  v0.1.2              ║
║  AI-Native Quantum Laboratory Operating System        ║
║                                                      ║
║  Developer: Jiaxiang Cong · Lingyuan Kong Lab        ║
║  Westlake University · Physics · CMP                  ║
║                                                      ║
║  Team: Jupiter · Venus · Mars · Mercury · Saturn      ║
║  Based on: Hermes Agent (Nous Research, MIT)          ║
╚══════════════════════════════════════════════════════╝
""")

async def start_lab(role: str = "all"):
    """启动实验室Agent系统"""
    from agents.roles.base import BaseRole, MessageBus
    from agents.roles.registry import RoleRegistry
    
    registry = RoleRegistry()
    bus = MessageBus()
    
    roles_config = {
        "orchestrator": "Orchestrator",
        "guard": "Guard",
        "mapper": "Mapper",
        "discovery": "Discovery",
        "compute": "Compute",
    }
    
    to_start = list(roles_config.keys()) if role == "all" else [role]
    
    print(f"\n{'='*60}")
    print(f"  Starting {len(to_start)} agent(s)...")
    print(f"{'='*60}\n")
    
    instances = []
    for r in to_start:
        try:
            inst = registry.create(roles_config[r])
            instances.append(inst)
            print(f"  ✓ {r}: {inst.agent_id}")
        except Exception as e:
            print(f"  ✗ {r}: {e}")
    
    if instances:
        print(f"\n  🟢 {len(instances)} agents running. WebSocket: ws://0.0.0.0:9876")
        print(f"  Press Ctrl+C to stop\n")
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n  Shutting down...")
            registry.shutdown_all()
            print("  All agents stopped. Goodbye.")
    else:
        print("  No agents started.")

async def start_single_agent(role: str, model: str = None):
    """启动单个Agent（Hermes模式）"""
    try:
        from core.integration import SingularityAgentWrapper
        agent = SingularityAgentWrapper(role_name=role)
        agent.initialize()
        
        print(f"  ⚛  {role} agent ready. Type /help for commands, /quit to exit.\n")
        
        while True:
            try:
                user_input = input("❯ ")
                if user_input.lower() in ("/quit", "/exit", "/q"):
                    break
                elif user_input.lower() == "/help":
                    print("  Commands: /quit, /help, /status")
                elif user_input.startswith("/"):
                    print(f"  Unknown command: {user_input}")
                elif user_input.strip():
                    response = agent.chat(user_input)
                    print(f"\n{response}\n")
            except (EOFError, KeyboardInterrupt):
                break
    except ImportError as e:
        print(f"  Hermes Agent not available: {e}")
        print(f"  Install: cd hermes-base && pip install -e .")

def main():
    parser = argparse.ArgumentParser(
        prog="singularity",
        description="Westlake Singularity — AI量子实验室操作系统",
        epilog="Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University"
    )
    
    parser.add_argument("--role", "-r", default="orchestrator",
                       choices=["orchestrator", "guard", "mapper", "discovery", "compute", "all"],
                       help="Agent角色 (default: orchestrator)")
    parser.add_argument("--single", "-s", action="store_true",
                       help="单Agent对话模式 (需要Hermes)")
    parser.add_argument("--version", "-v", action="store_true",
                       help="显示版本信息")
    parser.add_argument("--banner", "-b", action="store_true",
                       help="显示Banner")
    parser.add_argument("--status", action="store_true",
                       help="显示系统状态")
    
    args = parser.parse_args()
    
    if args.version:
        print("Westlake Singularity v0.1.2")
        print("Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University")
        print("Team: Jupiter(木星) Venus(金星) Mars(火星) Mercury(水星) Saturn(土星)")
        print("Based on: Hermes Agent v0.13.0 (Nous Research, MIT License)")
        return 0
    
    if args.banner:
        show_banner()
        return 0
    
    if args.status:
        show_banner()
        print("\n📊 System Status:")
        print(f"  Project root: {PROJECT_ROOT}")
        print(f"  Hermes base: {PROJECT_ROOT / 'hermes-base'}")
        print(f"  Modules: digital_twin, empire, agents, tools, perception, compute, bus, memory")
        
        # Check Hermes availability
        try:
            from core.integration import HERMES_AVAILABLE
            print(f"  Hermes Agent: {'✓ Available' if HERMES_AVAILABLE else '✗ Not installed'}")
        except ImportError:
            print(f"  Hermes Agent: ✗ Integration error")
        
        # Check module sizes
        for mod in ["digital_twin", "empire", "agents", "tools", "perception", "compute", "bus", "memory", "core"]:
            p = PROJECT_ROOT / mod
            if p.exists():
                py_count = len(list(p.rglob("*.py")))
                print(f"  {mod}/: {py_count} Python files")
        return 0
    
    show_banner()
    
    if args.single:
        asyncio.run(start_single_agent(args.role))
    else:
        asyncio.run(start_lab(args.role))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

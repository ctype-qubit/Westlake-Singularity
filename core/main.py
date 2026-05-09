"""Westlake Singularity — Main Entry Point
Usage: python -m core.main [--role ROLE] [--tui]
Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University
"""

import sys
import asyncio
import argparse

def show_banner():
    try:
        from branding.banner import show_banner
        show_banner(big=True)
    except ImportError:
        print("⚛  Westlake Singularity v0.1.0-alpha")
        print("   Developer: Jiaxiang Cong · Lingyuan Kong Lab")
        print("   Westlake University")

async def start_lab(role: str = "orchestrator"):
    """启动实验室Agent系统"""
    from agents.roles import RoleRegistry
    from agents.roles.bus import MessageBus
    
    registry = RoleRegistry()
    bus = MessageBus()
    
    roles_map = {
        "orchestrator": ("OrchestratorRole", {}),
        "guard": ("GuardRole", {}),
        "mapper": ("MapperRole", {}),
        "discovery": ("DiscoveryRole", {}),
        "compute": ("ComputeRole", {}),
    }
    
    print(f"\n{'='*60}")
    print(f"  Starting Westlake Singularity — {role.upper()} MODE")
    print(f"{'='*60}\n")
    
    if role == "all":
        instances = []
        for r_name, (cls_name, kwargs) in roles_map.items():
            inst = registry.create(cls_name.replace("Role", ""), **kwargs)
            instances.append(inst)
            print(f"  ✓ {r_name}: {inst.role_id}")
        await bus.start(instances)
    else:
        cls_name, kwargs = roles_map.get(role, roles_map["orchestrator"])
        inst = registry.create(cls_name.replace("Role", ""), **kwargs)
        print(f"  ✓ {role}: {inst.role_id}")
        await bus.start([inst])
    
    print(f"\n  All systems ready. WebSocket: ws://0.0.0.0:9876")
    print(f"  Press Ctrl+C to stop\n")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        registry.shutdown_all()

def main():
    parser = argparse.ArgumentParser(
        description="Westlake Singularity — AI量子实验室",
        epilog="Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University"
    )
    parser.add_argument("--role", "-r", default="orchestrator",
                       choices=["orchestrator", "guard", "mapper", "discovery", "compute", "all"],
                       help="Agent role to start")
    parser.add_argument("--tui", action="store_true", help="Launch TUI interface")
    parser.add_argument("--version", "-v", action="store_true", help="Show version")
    
    args = parser.parse_args()
    
    if args.version:
        print("Westlake Singularity v0.1.0-alpha")
        print("Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University")
        print("Team: Jupiter · Venus · Mars · Mercury · Saturn")
        sys.exit(0)
    
    show_banner()
    
    if args.tui:
        print("TUI mode coming soon...")
        sys.exit(0)
    
    asyncio.run(start_lab(args.role))

if __name__ == "__main__":
    main()

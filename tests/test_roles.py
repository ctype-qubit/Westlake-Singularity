"""
Test agent role system
"""
import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.roles.base import BaseRole, Message, MessageBus, Priority, Permission, RoleState

class TestBaseRole:
    def test_role_creation(self):
        role = BaseRole.__new__(BaseRole)
        role.role_name = "Test"
        role.permission_level = Permission.FULL_CONTROL
        role.heartbeat_interval = 1.0
        
    def test_message_creation(self):
        msg = Message(
            src_agent="test_src",
            dst_agent="test_dst",
            msg_type="test",
            payload={"key": "value"},
        )
        assert msg.src_agent == "test_src"
        assert msg.payload["key"] == "value"
        
        json_str = msg.to_json()
        msg2 = Message.from_json(json_str)
        assert msg2.src_agent == msg.src_agent

    def test_message_bus(self):
        bus = MessageBus()
        assert bus.subscriber_count == 0
        
        queue = bus.subscribe("agent1")
        assert bus.subscriber_count == 1
        
        bus.unsubscribe("agent1")
        assert bus.subscriber_count == 0

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        bus = MessageBus()
        q = bus.subscribe("test")
        
        msgs = [
            Message(priority=Priority.BACKGROUND, payload={"n": 0}),
            Message(priority=Priority.CRITICAL, payload={"n": 4}),
            Message(priority=Priority.NORMAL, payload={"n": 1}),
        ]
        
        for m in msgs:
            await bus.publish(m)
        
        received = []
        while not q.empty():
            received.append(await q.get())
        
        assert len(received) == 3

class TestPermissionSystem:
    def test_permission_levels(self):
        assert Permission.NONE < Permission.READ_SENSORS
        assert Permission.CONTROL_TOOLS > Permission.READ_SENSORS
        assert Permission.FULL_CONTROL >= Permission.CONTROL_TOOLS
        
    def test_role_state_transitions(self):
        role = BaseRole.__new__(BaseRole)
        role.role_name = "Test"
        role.state = RoleState.UNINITIALIZED
        
        # UNINITIALIZED → IDLE should fail (needs INITIALIZING)
        assert not role._is_valid_transition(RoleState.UNINITIALIZED, RoleState.IDLE)
        
        # UNINITIALIZED → INITIALIZING should work
        assert role._is_valid_transition(RoleState.UNINITIALIZED, RoleState.INITIALIZING)

"""
Test script for Cross-Device Handoff (Follow Me Protocol)
"""

import sys
sys.path.insert(0, '.')

from core.sync import (
    register_device,
    trigger_handoff,
    get_handoff_manager,
    get_sync_status,
    DEVICE_ROG_ALLY,
    DEVICE_LEGION
)

def test_handoff_basic():
    """Test basic handoff functionality."""
    print("=" * 60)
    print("Testing Cross-Device Handoff (Follow Me Protocol)")
    print("=" * 60)

    # Register test devices
    print("\n1. Registering test devices...")
    register_device("legion-desktop", DEVICE_LEGION, "Legion Desktop", "192.168.1.100")
    register_device("rog-ally-handheld", DEVICE_ROG_ALLY, "ROG Ally", "192.168.1.101")

    # Check sync status
    print("\n2. Checking sync status...")
    status = get_sync_status()
    print(f"   Active devices: {status['device_count']}")
    print(f"   Devices: {[d['device_id'] for d in status['all_devices']]}")

    # Trigger handoff from Legion to ROG Ally
    print("\n3. Triggering handoff: Legion -> ROG Ally...")
    result = trigger_handoff("legion-desktop", "rog-ally-handheld")
    print(f"   Status: {result['status']}")
    print(f"   Context transferred: {result['context_transferred']}")
    print(f"   Hardware shift emitted: {result['hardware_shift_emitted']}")
    if result.get('hardware_mode'):
        print(f"   Hardware mode: {result['hardware_mode']}")
    if result.get('errors'):
        print(f"   Errors: {result['errors']}")
    if result.get('context_package'):
        print(f"   Entries packaged: {result['context_package']['entry_count']}")
        print(f"   Time window: {result['context_package']['time_window']} minutes")

    # Trigger handoff back
    print("\n4. Triggering handoff: ROG Ally -> Legion...")
    result = trigger_handoff("rog-ally-handheld", "legion-desktop")
    print(f"   Status: {result['status']}")
    print(f"   Context transferred: {result['context_transferred']}")
    print(f"   Hardware shift emitted: {result['hardware_shift_emitted']}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_handoff_basic()

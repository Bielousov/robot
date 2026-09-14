"""Shared HailoRT VDevice singleton.

The Hailo-10H exposes a single physical device, and each `VDevice()` call
claims it exclusively - a second call while the first is still open fails.
"""

from hailo_platform import VDevice

_vdevice: "VDevice | None" = None

def get_vdevice() -> VDevice:
    global _vdevice
    if _vdevice is None:
        _vdevice = VDevice()
    return _vdevice

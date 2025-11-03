"""
Status tracking for event loading progress
Provides human-readable status updates for the frontend
"""

import threading
from datetime import datetime
from typing import Dict, Optional

# Global status tracker (thread-safe)
_status_lock = threading.Lock()
_current_status: Optional[Dict] = None


def set_status(step: int, total_steps: int, message: str, details: str = ""):
    """
    Set the current loading status
    
    Args:
        step: Current step number (1-based)
        total_steps: Total number of steps
        message: Plain language description of current step
        details: Additional details (optional)
    """
    global _current_status
    with _status_lock:
        _current_status = {
            "step": step,
            "total_steps": total_steps,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }


def get_status() -> Optional[Dict]:
    """Get the current status"""
    with _status_lock:
        return _current_status.copy() if _current_status else None


def clear_status():
    """Clear the status (when loading is complete)"""
    global _current_status
    with _status_lock:
        _current_status = None


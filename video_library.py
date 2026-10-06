"""
Video Library Facade for HICET Information AI Assistant.
========================================================
Delegates dynamically to video_utils for automatic video discovery from videos/.
No manual video list or hardcoded dictionary is required.
"""

from pathlib import Path
from typing import List, Dict

from video_utils import (
    BASE_DIR,
    VIDEOS_DIR,
    MEDIA_DIR,
    SUPPORTED_VIDEO_EXTENSIONS,
    get_available_videos,
    get_available_video_titles,
    is_safe_video_path,
    resolve_video_path,
)


def get_all_videos() -> List[Dict]:
    """Dynamically return all discovered videos from videos/."""
    return get_available_videos()


# Exported symbols for backward compatibility
__all__ = [
    "BASE_DIR",
    "MEDIA_DIR",
    "VIDEOS_DIR",
    "SUPPORTED_VIDEO_EXTENSIONS",
    "get_all_videos",
    "get_available_videos",
    "get_available_video_titles",
    "is_safe_video_path",
    "resolve_video_path",
]

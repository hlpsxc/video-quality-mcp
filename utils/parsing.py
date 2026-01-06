"""Parsing utilities for FFmpeg/ffprobe output."""

from typing import Dict, Any, Optional


def parse_duration(duration_str: Optional[str]) -> float:
    """
    Parse duration string from ffprobe to seconds.
    
    Args:
        duration_str: Duration string (e.g., "12.345000")
        
    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0.0
    try:
        return float(duration_str)
    except (ValueError, TypeError):
        return 0.0


def parse_bitrate(bitrate_str: Optional[str]) -> int:
    """
    Parse bitrate string to integer bits per second.
    
    Args:
        bitrate_str: Bitrate string (e.g., "4200000")
        
    Returns:
        Bitrate in bits per second
    """
    if not bitrate_str:
        return 0
    try:
        return int(bitrate_str)
    except (ValueError, TypeError):
        return 0


def parse_fps(fps_str: Optional[str]) -> float:
    """
    Parse frame rate string to float.
    
    Args:
        fps_str: Frame rate string (e.g., "29.97" or "30000/1001")
        
    Returns:
        Frame rate as float
    """
    if not fps_str:
        return 0.0
    
    try:
        # Handle fraction format (e.g., "30000/1001")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            return float(num) / float(den)
        return float(fps_str)
    except (ValueError, TypeError):
        return 0.0


def get_video_stream(streams: list) -> Optional[Dict[str, Any]]:
    """
    Extract video stream from streams list.
    
    Args:
        streams: List of stream dictionaries from ffprobe
        
    Returns:
        Video stream dictionary or None
    """
    for stream in streams:
        if stream.get("codec_type") == "video":
            return stream
    return None


def get_audio_stream(streams: list) -> Optional[Dict[str, Any]]:
    """
    Extract audio stream from streams list.
    
    Args:
        streams: List of stream dictionaries from ffprobe
        
    Returns:
        Audio stream dictionary or None
    """
    for stream in streams:
        if stream.get("codec_type") == "audio":
            return stream
    return None


def parse_frame_type(pict_type: Optional[str]) -> str:
    """
    Parse frame picture type.
    
    Args:
        pict_type: Picture type string (I, P, B)
        
    Returns:
        Frame type (I, P, B, or Unknown)
    """
    if not pict_type:
        return "Unknown"
    
    pict_type = pict_type.upper()
    if pict_type in ["I", "P", "B"]:
        return pict_type
    return "Unknown"


def parse_keyframe_flag(flags: Optional[str]) -> bool:
    """
    Parse keyframe flag from packet flags.
    
    Args:
        flags: Flags string (e.g., "K_")
        
    Returns:
        True if keyframe, False otherwise
    """
    if not flags:
        return False
    return "K" in flags or "key_frame" in flags.lower()


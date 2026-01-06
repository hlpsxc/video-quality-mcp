"""Video metadata analysis tool."""

import os
from typing import Dict, Any
from utils.ffmpeg import get_video_info, FFmpegError
from utils.parsing import (
    parse_duration,
    parse_bitrate,
    parse_fps,
    get_video_stream
)


def analyze_video_metadata(path: str) -> Dict[str, Any]:
    """
    Analyze video metadata and encoding information.
    
    Args:
        path: Path to video file
        
    Returns:
        Dictionary containing format and video stream information
        
    Raises:
        FFmpegError: If video file cannot be analyzed
    """
    try:
        info = get_video_info(path)
        
        format_info = info.get("format", {})
        streams = info.get("streams", [])
        
        video_stream = get_video_stream(streams)
        if not video_stream:
            raise FFmpegError("No video stream found in file")
        
        # Parse format information
        duration = parse_duration(format_info.get("duration"))
        size = int(format_info.get("size", 0))
        bitrate = parse_bitrate(format_info.get("bitrate"))
        container = format_info.get("format_name", "unknown").split(",")[0]
        
        # Parse video stream information
        codec = video_stream.get("codec_name", "unknown")
        profile = video_stream.get("profile", "unknown")
        level = video_stream.get("level", "unknown")
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        fps = parse_fps(video_stream.get("r_frame_rate"))
        pix_fmt = video_stream.get("pix_fmt", "unknown")
        
        # Determine bit depth from pixel format
        bit_depth = 8
        if "10" in pix_fmt or "12" in pix_fmt or "16" in pix_fmt:
            if "10" in pix_fmt:
                bit_depth = 10
            elif "12" in pix_fmt:
                bit_depth = 12
            elif "16" in pix_fmt:
                bit_depth = 16
        
        result = {
            "format": {
                "container": container,
                "duration": round(duration, 3),
                "size": size,
                "bitrate": bitrate
            },
            "video": {
                "codec": codec,
                "profile": profile,
                "level": str(level) if level != "unknown" else "unknown",
                "width": width,
                "height": height,
                "fps": round(fps, 3),
                "pix_fmt": pix_fmt,
                "bit_depth": bit_depth
            }
        }
        
        return result
        
    except FFmpegError:
        raise
    except Exception as e:
        raise FFmpegError(f"Failed to analyze metadata: {str(e)}")


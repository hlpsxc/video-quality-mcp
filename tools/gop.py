"""GOP structure analysis tool."""

from typing import Dict, Any, List
from utils.ffmpeg import get_frame_info, get_packets, FFmpegError
from utils.parsing import parse_frame_type, parse_duration


def analyze_gop_structure(path: str) -> Dict[str, Any]:
    """
    Analyze GOP structure and frame distribution.
    
    Args:
        path: Path to video file
        
    Returns:
        Dictionary containing frame distribution and GOP statistics
        
    Raises:
        FFmpegError: If video file cannot be analyzed
    """
    try:
        # Get frame information
        frames = get_frame_info(path)
        
        # Count frame types
        frame_counts = {"I": 0, "P": 0, "B": 0}
        keyframe_timestamps = []
        gop_lengths = []
        current_gop = 0
        
        for frame in frames:
            frame_type = parse_frame_type(frame.get("pict_type"))
            if frame_type in frame_counts:
                frame_counts[frame_type] += 1
            
            # Track keyframes and GOP lengths
            if frame.get("key_frame") == 1 or frame_type == "I":
                pts_time = parse_duration(frame.get("pkt_pts_time"))
                if pts_time is not None and pts_time >= 0:
                    keyframe_timestamps.append(round(pts_time, 3))
                
                if current_gop > 0:
                    gop_lengths.append(current_gop)
                current_gop = 1
            else:
                current_gop += 1
        
        # Add last GOP if video doesn't end with keyframe
        if current_gop > 0:
            gop_lengths.append(current_gop)
        
        # Calculate GOP statistics
        if gop_lengths:
            avg_gop = sum(gop_lengths) / len(gop_lengths)
            min_gop = min(gop_lengths)
            max_gop = max(gop_lengths)
        else:
            avg_gop = 0
            min_gop = 0
            max_gop = 0
        
        result = {
            "frame_distribution": frame_counts,
            "gop_stats": {
                "avg_gop": round(avg_gop, 1),
                "min_gop": min_gop,
                "max_gop": max_gop
            },
            "keyframe_timestamps": keyframe_timestamps[:100]  # Limit to first 100
        }
        
        return result
        
    except FFmpegError:
        raise
    except Exception as e:
        raise FFmpegError(f"Failed to analyze GOP structure: {str(e)}")


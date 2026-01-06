"""FFmpeg and ffprobe command wrapper utilities."""

import json
import subprocess
import os
from typing import Dict, List, Optional, Any, Tuple


class FFmpegError(Exception):
    """Custom exception for FFmpeg-related errors."""
    pass


def run_command(cmd: List[str], timeout: Optional[int] = None) -> Tuple[str, str]:
    """
    Execute a command and return stdout and stderr.
    
    Args:
        cmd: Command and arguments as a list
        timeout: Optional timeout in seconds
        
    Returns:
        Tuple of (stdout, stderr)
        
    Raises:
        FFmpegError: If command execution fails
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        
        if result.returncode != 0:
            raise FFmpegError(
                f"Command failed with return code {result.returncode}:\n"
                f"Command: {' '.join(cmd)}\n"
                f"Stderr: {result.stderr}"
            )
        
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        raise FFmpegError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
    except FileNotFoundError:
        raise FFmpegError("FFmpeg/ffprobe not found. Please ensure it's installed and in PATH.")


def get_video_info(path: str) -> Dict[str, Any]:
    """
    Get comprehensive video information using ffprobe.
    
    Args:
        path: Path to video file
        
    Returns:
        Dictionary containing format and stream information
    """
    if not os.path.exists(path):
        raise FFmpegError(f"Video file not found: {path}")
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path
    ]
    
    stdout, _ = run_command(cmd, timeout=60)
    
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        raise FFmpegError(f"Failed to parse ffprobe output: {e}")


def get_frame_info(path: str) -> List[Dict[str, Any]]:
    """
    Get frame-by-frame information including frame types.
    
    Args:
        path: Path to video file
        
    Returns:
        List of frame dictionaries with type, pts, etc.
    """
    if not os.path.exists(path):
        raise FFmpegError(f"Video file not found: {path}")
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_frames",
        "-select_streams", "v:0",
        path
    ]
    
    stdout, _ = run_command(cmd, timeout=120)
    
    try:
        data = json.loads(stdout)
        return data.get("frames", [])
    except json.JSONDecodeError as e:
        raise FFmpegError(f"Failed to parse frame info: {e}")


def get_packets(path: str) -> List[Dict[str, Any]]:
    """
    Get packet information including keyframe flags.
    
    Args:
        path: Path to video file
        
    Returns:
        List of packet dictionaries
    """
    if not os.path.exists(path):
        raise FFmpegError(f"Video file not found: {path}")
    
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_packets",
        "-select_streams", "v:0",
        path
    ]
    
    stdout, _ = run_command(cmd, timeout=120)
    
    try:
        data = json.loads(stdout)
        return data.get("packets", [])
    except json.JSONDecodeError as e:
        raise FFmpegError(f"Failed to parse packet info: {e}")


def extract_frame(path: str, timestamp: float, output_path: str) -> str:
    """
    Extract a single frame at specified timestamp.
    
    Args:
        path: Input video path
        timestamp: Timestamp in seconds
        output_path: Output image path
        
    Returns:
        Path to extracted frame
    """
    if not os.path.exists(path):
        raise FFmpegError(f"Video file not found: {path}")
    
    cmd = [
        "ffmpeg",
        "-i", path,
        "-ss", str(timestamp),
        "-vframes", "1",
        "-y",
        output_path
    ]
    
    run_command(cmd, timeout=30)
    
    if not os.path.exists(output_path):
        raise FFmpegError(f"Failed to extract frame to {output_path}")
    
    return output_path


def calculate_psnr(reference: str, distorted: str) -> Dict[str, float]:
    """
    Calculate PSNR using FFmpeg.
    
    Args:
        reference: Reference video path
        distorted: Distorted video path
        
    Returns:
        Dictionary with Y, U, V PSNR values
    """
    if not os.path.exists(reference):
        raise FFmpegError(f"Reference video not found: {reference}")
    if not os.path.exists(distorted):
        raise FFmpegError(f"Distorted video not found: {distorted}")
    
    cmd = [
        "ffmpeg",
        "-i", distorted,
        "-i", reference,
        "-lavfi", "psnr=stats_file=psnr.log",
        "-f", "null",
        "-"
    ]
    
    try:
        run_command(cmd, timeout=300)
        
        # Parse PSNR log
        if os.path.exists("psnr.log"):
            with open("psnr.log", "r") as f:
                lines = f.readlines()
            
            # Get average PSNR from last line
            if lines:
                last_line = lines[-1].strip()
                # Format: n:Y:U:V
                parts = last_line.split(":")
                if len(parts) >= 4:
                    return {
                        "y": float(parts[1]) if parts[1] != "inf" else 100.0,
                        "u": float(parts[2]) if parts[2] != "inf" else 100.0,
                        "v": float(parts[3]) if parts[3] != "inf" else 100.0,
                    }
        
        raise FFmpegError("Failed to parse PSNR output")
    finally:
        if os.path.exists("psnr.log"):
            os.remove("psnr.log")


def calculate_ssim(reference: str, distorted: str) -> float:
    """
    Calculate SSIM using FFmpeg.
    
    Args:
        reference: Reference video path
        distorted: Distorted video path
        
    Returns:
        SSIM score (0-1)
    """
    if not os.path.exists(reference):
        raise FFmpegError(f"Reference video not found: {reference}")
    if not os.path.exists(distorted):
        raise FFmpegError(f"Distorted video not found: {distorted}")
    
    cmd = [
        "ffmpeg",
        "-i", distorted,
        "-i", reference,
        "-lavfi", "ssim=stats_file=ssim.log",
        "-f", "null",
        "-"
    ]
    
    try:
        run_command(cmd, timeout=300)
        
        # Parse SSIM log
        if os.path.exists("ssim.log"):
            with open("ssim.log", "r") as f:
                lines = f.readlines()
            
            # Get average SSIM from last line
            if lines:
                last_line = lines[-1].strip()
                # Format: n:Y:U:V:All
                parts = last_line.split(":")
                if len(parts) >= 5:
                    return float(parts[4])
        
        raise FFmpegError("Failed to parse SSIM output")
    finally:
        if os.path.exists("ssim.log"):
            os.remove("ssim.log")


def calculate_vmaf(reference: str, distorted: str, model: str = "vmaf_v0.6.1") -> Dict[str, Any]:
    """
    Calculate VMAF using FFmpeg (requires libvmaf).
    
    Args:
        reference: Reference video path
        distorted: Distorted video path
        model: VMAF model version
        
    Returns:
        Dictionary with VMAF score and model info
    """
    if not os.path.exists(reference):
        raise FFmpegError(f"Reference video not found: {reference}")
    if not os.path.exists(distorted):
        raise FFmpegError(f"Distorted video not found: {distorted}")
    
    cmd = [
        "ffmpeg",
        "-i", distorted,
        "-i", reference,
        "-lavfi", f"libvmaf=model=version={model}:log_path=vmaf.log",
        "-f", "null",
        "-"
    ]
    
    try:
        run_command(cmd, timeout=600)
        
        # Parse VMAF log
        if os.path.exists("vmaf.log"):
            with open("vmaf.log", "r") as f:
                content = f.read()
            
            # Extract average VMAF score
            # VMAF log format: frame_number VMAF_score
            lines = content.strip().split("\n")
            if lines:
                scores = []
                for line in lines[1:]:  # Skip header
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            scores.append(float(parts[1]))
                        except ValueError:
                            continue
                
                if scores:
                    avg_score = sum(scores) / len(scores)
                    return {
                        "score": avg_score,
                        "model": model
                    }
        
        raise FFmpegError("Failed to parse VMAF output. Ensure libvmaf is installed.")
    except FFmpegError:
        # If VMAF fails, return a fallback
        raise FFmpegError("VMAF calculation failed. Ensure libvmaf is installed and videos are compatible.")
    finally:
        if os.path.exists("vmaf.log"):
            os.remove("vmaf.log")


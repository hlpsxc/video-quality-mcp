"""Video quality metrics comparison tool."""

from typing import Dict, Any
from utils.ffmpeg import (
    calculate_psnr,
    calculate_ssim,
    calculate_vmaf,
    FFmpegError
)


def compare_quality_metrics(reference: str, distorted: str) -> Dict[str, Any]:
    """
    Compare quality metrics between reference and distorted video.
    
    Args:
        reference: Path to reference video
        distorted: Path to distorted/transcoded video
        
    Returns:
        Dictionary containing PSNR, SSIM, and VMAF scores
        
    Raises:
        FFmpegError: If comparison fails
    """
    result = {
        "psnr": None,
        "ssim": None,
        "vmaf": None
    }
    
    errors = []
    
    # Calculate PSNR
    try:
        psnr_result = calculate_psnr(reference, distorted)
        result["psnr"] = {
            "y": round(psnr_result["y"], 2),
            "u": round(psnr_result["u"], 2),
            "v": round(psnr_result["v"], 2)
        }
    except FFmpegError as e:
        errors.append(f"PSNR calculation failed: {str(e)}")
    except Exception as e:
        errors.append(f"PSNR calculation error: {str(e)}")
    
    # Calculate SSIM
    try:
        ssim_score = calculate_ssim(reference, distorted)
        result["ssim"] = round(ssim_score, 4)
    except FFmpegError as e:
        errors.append(f"SSIM calculation failed: {str(e)}")
    except Exception as e:
        errors.append(f"SSIM calculation error: {str(e)}")
    
    # Calculate VMAF
    try:
        vmaf_result = calculate_vmaf(reference, distorted)
        result["vmaf"] = {
            "score": round(vmaf_result["score"], 2),
            "model": vmaf_result["model"]
        }
    except FFmpegError as e:
        errors.append(f"VMAF calculation failed: {str(e)}")
    except Exception as e:
        errors.append(f"VMAF calculation error: {str(e)}")
    
    # If all metrics failed, raise error
    if not result["psnr"] and not result["ssim"] and not result["vmaf"]:
        raise FFmpegError(f"All quality metrics failed: {'; '.join(errors)}")
    
    # Add warnings if some metrics failed
    if errors:
        result["warnings"] = errors
    
    return result


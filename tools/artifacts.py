"""Artifact and perceptual quality analysis tool."""

import os
import tempfile
import numpy as np
import cv2
from typing import Dict, Any, Optional
from utils.ffmpeg import extract_frame, get_video_info, FFmpegError
from utils.parsing import get_video_stream, parse_duration


def analyze_artifacts(
    target: str,
    reference: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze video artifacts and perceptual quality proxies.
    
    Args:
        target: Path to target video
        reference: Optional path to reference video for comparison
        
    Returns:
        Dictionary containing artifact scores and analysis
    """
    mode = "compare" if reference else "single"
    
    try:
        if mode == "compare":
            target_scores = _analyze_single_video(target)
            reference_scores = _analyze_single_video(reference)
            
            # Calculate deltas
            artifact_deltas = {}
            for key in target_scores:
                if key in reference_scores and "score" in target_scores[key]:
                    target_val = target_scores[key]["score"]
                    ref_val = reference_scores[key]["score"]
                    delta = target_val - ref_val
                    
                    artifact_deltas[key] = {
                        "delta": round(delta, 3),
                        "impact": "worse" if delta > 0.05 else "better" if delta < -0.05 else "neutral"
                    }
            
            # Determine risk summary
            risk_summary = _calculate_risk_summary(target_scores, reference_scores, artifact_deltas)
            
            result = {
                "mode": mode,
                "artifact_scores": target_scores,
                "artifact_deltas": artifact_deltas,
                "risk_summary": risk_summary,
                "notes": _generate_notes(artifact_deltas, risk_summary)
            }
        else:
            target_scores = _analyze_single_video(target)
            risk_summary = _calculate_single_risk_summary(target_scores)
            
            result = {
                "mode": mode,
                "artifact_scores": target_scores,
                "artifact_deltas": {},
                "risk_summary": risk_summary,
                "notes": _generate_single_notes(target_scores, risk_summary)
            }
        
        return result
        
    except Exception as e:
        raise FFmpegError(f"Failed to analyze artifacts: {str(e)}")


def _analyze_single_video(path: str) -> Dict[str, Any]:
    """Analyze artifacts for a single video."""
    scores = {}
    
    # Extract sample frames for analysis
    info = get_video_info(path)
    video_stream = get_video_stream(info.get("streams", []))
    if not video_stream:
        raise FFmpegError("No video stream found")
    
    duration = parse_duration(info.get("format", {}).get("duration"))
    
    # Sample frames at 10%, 50%, 90% of duration
    sample_times = [duration * 0.1, duration * 0.5, duration * 0.9]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        frame_paths = []
        for t in sample_times:
            if t < duration:
                frame_path = os.path.join(tmpdir, f"frame_{t:.2f}.png")
                try:
                    extract_frame(path, t, frame_path)
                    frame_paths.append(frame_path)
                except:
                    continue
        
        if not frame_paths:
            raise FFmpegError("Failed to extract sample frames")
        
        # Analyze each frame and average
        all_scores = {
            "blur": [],
            "blocking": [],
            "ringing": [],
            "banding": [],
            "dark_detail_loss": []
        }
        
        for frame_path in frame_paths:
            frame = cv2.imread(frame_path)
            if frame is None:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Blur detection (Laplacian variance)
            blur_score = _detect_blur(gray)
            all_scores["blur"].append(blur_score)
            
            # Blocking detection (DCT-based)
            blocking_score = _detect_blocking(gray)
            all_scores["blocking"].append(blocking_score)
            
            # Ringing detection (high-frequency edge analysis)
            ringing_score = _detect_ringing(gray)
            all_scores["ringing"].append(ringing_score)
            
            # Banding detection (color gradient analysis)
            banding_risk = _detect_banding(frame)
            all_scores["banding"].append(banding_risk)
            
            # Dark detail loss (histogram analysis)
            dark_score = _detect_dark_detail_loss(gray)
            all_scores["dark_detail_loss"].append(dark_score)
        
        # Average scores
        for key, values in all_scores.items():
            if values:
                avg = np.mean(values)
                if key == "banding":
                    # Banding uses risk levels
                    if avg < 0.3:
                        level = "low"
                    elif avg < 0.6:
                        level = "medium"
                    else:
                        level = "high"
                    scores[key] = {"risk": level}
                else:
                    # Other metrics use scores
                    if avg < 0.3:
                        level = "low"
                    elif avg < 0.6:
                        level = "medium"
                    else:
                        level = "high"
                    
                    scores[key] = {
                        "score": round(float(avg), 3),
                        "level": level,
                        "description": _get_artifact_description(key, avg)
                    }
    
    return scores


def _detect_blur(gray: np.ndarray) -> float:
    """Detect blur using Laplacian variance."""
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    
    # Normalize: lower variance = more blur
    # Typical range: 0-1000+, normalize to 0-1
    normalized = 1.0 - min(variance / 500.0, 1.0)
    return normalized


def _detect_blocking(gray: np.ndarray) -> float:
    """Detect blocking artifacts using DCT analysis."""
    # Divide into 8x8 blocks (typical macroblock size)
    h, w = gray.shape
    block_size = 8
    
    blocking_score = 0.0
    block_count = 0
    
    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block = gray[y:y+block_size, x:x+block_size].astype(np.float32)
            
            # DCT
            dct_block = cv2.dct(block)
            
            # High frequency energy (indicative of blocking)
            # Focus on high-frequency coefficients
            hf_energy = np.sum(np.abs(dct_block[4:, 4:]))
            total_energy = np.sum(np.abs(dct_block))
            
            if total_energy > 0:
                hf_ratio = hf_energy / total_energy
                blocking_score += hf_ratio
                block_count += 1
    
    if block_count > 0:
        avg_score = blocking_score / block_count
        # Normalize to 0-1 range
        return min(avg_score * 2.0, 1.0)
    
    return 0.0


def _detect_ringing(gray: np.ndarray) -> float:
    """Detect ringing artifacts near edges."""
    # Apply Sobel to detect edges
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    edges = np.sqrt(sobelx**2 + sobely**2)
    
    # Threshold for strong edges
    edge_threshold = np.percentile(edges, 95)
    edge_mask = edges > edge_threshold
    
    # Analyze oscillations near edges (ringing indicator)
    # Use high-pass filter
    kernel = np.array([[-1, -1, -1],
                       [-1,  8, -1],
                       [-1, -1, -1]])
    high_pass = cv2.filter2D(gray.astype(np.float32), -1, kernel)
    
    # Measure high-frequency energy near edges
    if np.any(edge_mask):
        ringing_energy = np.mean(np.abs(high_pass[edge_mask]))
        # Normalize
        return min(ringing_energy / 50.0, 1.0)
    
    return 0.0


def _detect_banding(bgr: np.ndarray) -> float:
    """Detect color banding (posterization)."""
    # Convert to LAB color space for better gradient analysis
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0]
    
    # Calculate gradients
    grad_x = cv2.Sobel(l_channel, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(l_channel, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Banding shows as areas with very low gradient (flat regions)
    # but with sudden jumps (quantization)
    low_gradient_mask = gradient_magnitude < 5
    flat_regions = l_channel[low_gradient_mask]
    
    if len(flat_regions) > 0:
        # Check for quantization (few distinct values)
        unique_values = len(np.unique(flat_regions))
        total_pixels = len(flat_regions)
        quantization_ratio = unique_values / total_pixels if total_pixels > 0 else 0
        
        # Lower ratio = more banding
        banding_score = 1.0 - min(quantization_ratio * 10, 1.0)
        return banding_score
    
    return 0.0


def _detect_dark_detail_loss(gray: np.ndarray) -> float:
    """Detect loss of detail in dark regions."""
    # Focus on dark regions (bottom 30% of brightness)
    dark_threshold = np.percentile(gray, 30)
    dark_mask = gray < dark_threshold
    
    if not np.any(dark_mask):
        return 0.0
    
    dark_region = gray[dark_mask]
    
    # Calculate local variance in dark regions
    # Low variance = loss of detail
    kernel = np.ones((5, 5), np.float32) / 25
    local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
    local_var = cv2.filter2D((gray.astype(np.float32) - local_mean)**2, -1, kernel)
    
    dark_variance = np.mean(local_var[dark_mask])
    
    # Normalize: very low variance = high detail loss
    normalized = 1.0 - min(dark_variance / 100.0, 1.0)
    return normalized


def _get_artifact_description(artifact_type: str, score: float) -> str:
    """Generate description for artifact score."""
    descriptions = {
        "blur": {
            "low": "边缘清晰，细节保持良好",
            "medium": "边缘锐度不足，细节略显模糊",
            "high": "明显模糊，细节严重丢失"
        },
        "blocking": {
            "low": "宏块结构不明显",
            "medium": "轻微宏块效应",
            "high": "宏块结构明显，可感知压缩痕迹"
        },
        "ringing": {
            "low": "振铃效应不明显",
            "medium": "边缘存在轻微振铃",
            "high": "明显振铃伪影"
        },
        "dark_detail_loss": {
            "low": "暗部细节保持良好",
            "medium": "暗部细节部分丢失",
            "high": "暗部细节严重丢失"
        }
    }
    
    level = "low" if score < 0.3 else "medium" if score < 0.6 else "high"
    return descriptions.get(artifact_type, {}).get(level, "")


def _calculate_risk_summary(
    target_scores: Dict[str, Any],
    reference_scores: Dict[str, Any],
    deltas: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate risk summary for comparison mode."""
    worse_artifacts = []
    for key, delta_info in deltas.items():
        if delta_info.get("impact") == "worse" and abs(delta_info.get("delta", 0)) > 0.1:
            worse_artifacts.append(key)
    
    # Determine overall risk
    if len(worse_artifacts) >= 3:
        overall_risk = "high"
    elif len(worse_artifacts) >= 1:
        overall_risk = "medium"
    else:
        overall_risk = "low"
    
    # Generate likely causes
    likely_causes = []
    if "blocking" in worse_artifacts:
        likely_causes.append("码率不足")
        likely_causes.append("量化参数偏高")
    if "dark_detail_loss" in worse_artifacts:
        likely_causes.append("VBV 约束过紧")
        likely_causes.append("暗部量化参数设置不当")
    if "blur" in worse_artifacts:
        likely_causes.append("编码器预设过于激进")
    if "banding" in worse_artifacts:
        likely_causes.append("色深不足")
        likely_causes.append("量化步长过大")
    
    if not likely_causes:
        likely_causes.append("转码参数需要优化")
    
    return {
        "overall_risk": overall_risk,
        "dominant_issues": worse_artifacts[:3],
        "likely_causes": likely_causes[:3]
    }


def _calculate_single_risk_summary(scores: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate risk summary for single video mode."""
    high_risk_artifacts = []
    for key, value in scores.items():
        if isinstance(value, dict):
            level = value.get("level") or value.get("risk")
            if level == "high":
                high_risk_artifacts.append(key)
    
    overall_risk = "high" if len(high_risk_artifacts) >= 2 else "medium" if len(high_risk_artifacts) >= 1 else "low"
    
    return {
        "overall_risk": overall_risk,
        "dominant_issues": high_risk_artifacts[:3],
        "likely_causes": []
    }


def _generate_notes(deltas: Dict[str, Any], risk_summary: Dict[str, Any]) -> list:
    """Generate analysis notes for comparison mode."""
    notes = []
    
    if risk_summary.get("overall_risk") == "high":
        notes.append("转码质量下降明显，建议重新评估编码参数")
    
    for artifact, delta_info in deltas.items():
        if delta_info.get("impact") == "worse":
            delta_val = delta_info.get("delta", 0)
            if delta_val > 0.2:
                notes.append(f"{artifact} 显著恶化 (delta: +{delta_val:.2f})")
    
    return notes


def _generate_single_notes(scores: Dict[str, Any], risk_summary: Dict[str, Any]) -> list:
    """Generate analysis notes for single video mode."""
    notes = []
    
    for key, value in scores.items():
        if isinstance(value, dict):
            level = value.get("level") or value.get("risk")
            if level == "high":
                notes.append(f"{key} 风险较高")
    
    return notes


"""Transcode comparison summary tool."""

from typing import Dict, Any, List
from tools.metadata import analyze_video_metadata
from tools.quality import compare_quality_metrics
from tools.artifacts import analyze_artifacts
from utils.ffmpeg import FFmpegError


def summarize_transcode_comparison(source: str, transcoded: str) -> Dict[str, Any]:
    """
    Generate comprehensive transcode comparison summary.
    
    Args:
        source: Path to source video
        transcoded: Path to transcoded video
        
    Returns:
        Dictionary containing verdict, quality changes, issues, and recommendations
    """
    try:
        # Get metadata for both videos
        source_meta = analyze_video_metadata(source)
        transcoded_meta = analyze_video_metadata(transcoded)
        
        # Calculate quality metrics
        quality_metrics = compare_quality_metrics(source, transcoded)
        
        # Analyze artifacts
        artifact_analysis = analyze_artifacts(transcoded, source)
        
        # Calculate bitrate saving
        source_bitrate = source_meta["format"]["bitrate"]
        transcoded_bitrate = transcoded_meta["format"]["bitrate"]
        bitrate_saving = 0
        if source_bitrate > 0:
            bitrate_saving = round((1 - transcoded_bitrate / source_bitrate) * 100, 1)
        
        # Get VMAF delta
        # VMAF is calculated as reference vs distorted, so the score represents
        # the quality of transcoded relative to source (source is reference)
        vmaf_delta = None
        if quality_metrics.get("vmaf"):
            transcoded_vmaf = quality_metrics["vmaf"]["score"]
            # VMAF score is already relative to reference (source)
            # Lower score means worse quality, so delta is negative
            vmaf_delta = round(transcoded_vmaf - 100.0, 1)
        
        # Determine verdict
        verdict = _determine_verdict(quality_metrics, artifact_analysis, vmaf_delta)
        
        # Extract key issues
        key_issues = _extract_key_issues(artifact_analysis, quality_metrics)
        
        # Generate recommendations
        recommendations = _generate_recommendations(
            artifact_analysis,
            quality_metrics,
            source_meta,
            transcoded_meta
        )
        
        result = {
            "verdict": verdict,
            "quality_change": {
                "vmaf_delta": vmaf_delta,
                "bitrate_saving": bitrate_saving
            },
            "key_issues": key_issues,
            "recommendations": recommendations
        }
        
        # Add detailed metrics if available
        if quality_metrics.get("psnr"):
            result["quality_change"]["psnr_y"] = quality_metrics["psnr"]["y"]
        if quality_metrics.get("ssim"):
            result["quality_change"]["ssim"] = quality_metrics["ssim"]
        
        return result
        
    except FFmpegError:
        raise
    except Exception as e:
        raise FFmpegError(f"Failed to generate summary: {str(e)}")


def _determine_verdict(
    quality_metrics: Dict[str, Any],
    artifact_analysis: Dict[str, Any],
    vmaf_delta: float
) -> str:
    """Determine overall verdict."""
    risk = artifact_analysis.get("risk_summary", {}).get("overall_risk", "low")
    
    # Check VMAF
    if vmaf_delta is not None:
        if vmaf_delta < -10:
            return "error"
        elif vmaf_delta < -5:
            return "warning"
        elif vmaf_delta < -2:
            return "notice"
    
    # Check risk level
    if risk == "high":
        return "warning"
    elif risk == "medium":
        return "notice"
    
    # Check PSNR if available
    if quality_metrics.get("psnr"):
        psnr_y = quality_metrics["psnr"]["y"]
        if psnr_y < 30:
            return "warning"
        elif psnr_y < 35:
            return "notice"
    
    return "acceptable"


def _extract_key_issues(
    artifact_analysis: Dict[str, Any],
    quality_metrics: Dict[str, Any]
) -> List[str]:
    """Extract key issues from analysis."""
    issues = []
    
    # From artifact analysis
    risk_summary = artifact_analysis.get("risk_summary", {})
    dominant_issues = risk_summary.get("dominant_issues", [])
    
    issue_descriptions = {
        "blur": "画面模糊，细节丢失",
        "blocking": "宏块效应增强",
        "ringing": "振铃伪影明显",
        "banding": "色带现象",
        "dark_detail_loss": "暗部细节明显丢失"
    }
    
    for issue in dominant_issues:
        desc = issue_descriptions.get(issue, issue)
        if desc not in issues:
            issues.append(desc)
    
    # From quality metrics
    if quality_metrics.get("psnr"):
        psnr_y = quality_metrics["psnr"]["y"]
        if psnr_y < 30:
            issues.append("PSNR 过低，画质下降明显")
    
    if quality_metrics.get("vmaf"):
        vmaf_score = quality_metrics["vmaf"]["score"]
        if vmaf_score < 80:
            issues.append("VMAF 评分较低")
    
    return issues[:5]  # Limit to 5 issues


def _generate_recommendations(
    artifact_analysis: Dict[str, Any],
    quality_metrics: Dict[str, Any],
    source_meta: Dict[str, Any],
    transcoded_meta: Dict[str, Any]
) -> List[str]:
    """Generate encoding parameter recommendations."""
    recommendations = []
    
    # Check artifact deltas
    artifact_deltas = artifact_analysis.get("artifact_deltas", {})
    risk_summary = artifact_analysis.get("risk_summary", {})
    likely_causes = risk_summary.get("likely_causes", [])
    
    # Blocking issues
    if "blocking" in artifact_deltas:
        delta = artifact_deltas["blocking"].get("delta", 0)
        if delta > 0.2:
            recommendations.append("降低 CRF 值（提高码率）")
            recommendations.append("调整量化参数，降低 QP")
    
    # Dark detail loss
    if "dark_detail_loss" in artifact_deltas:
        delta = artifact_deltas["dark_detail_loss"].get("delta", 0)
        if delta > 0.2:
            recommendations.append("放宽 VBV 缓冲区限制")
            recommendations.append("启用 aq-mode=3（自适应量化）")
            recommendations.append("调整暗部量化偏移")
    
    # Blur issues
    if "blur" in artifact_deltas:
        delta = artifact_deltas["blur"].get("delta", 0)
        if delta > 0.15:
            recommendations.append("使用更保守的编码预设")
            recommendations.append("提高码率或降低 CRF")
    
    # Banding issues
    if "banding" in artifact_deltas:
        recommendations.append("增加色深（10-bit 编码）")
        recommendations.append("使用更精细的量化步长")
    
    # General recommendations based on causes
    if "码率不足" in likely_causes:
        recommendations.append("提高目标码率")
    if "VBV 约束过紧" in likely_causes:
        recommendations.append("放宽 VBV 缓冲区大小")
    if "量化参数偏高" in likely_causes:
        recommendations.append("降低 CRF/QP 值")
    
    # If no specific issues, provide general advice
    if not recommendations:
        recommendations.append("转码质量可接受，可进一步优化编码参数以平衡质量与码率")
    
    # Remove duplicates and limit
    unique_recs = []
    for rec in recommendations:
        if rec not in unique_recs:
            unique_recs.append(rec)
    
    return unique_recs[:5]  # Limit to 5 recommendations


"""MCP Server implementation with tool registration."""

import json
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.metadata import analyze_video_metadata
from tools.gop import analyze_gop_structure
from tools.quality import compare_quality_metrics
from tools.artifacts import analyze_artifacts
from tools.summary import summarize_transcode_comparison
from utils.ffmpeg import FFmpegError


# Create MCP server instance
app = Server("video-quality-mcp")


def create_error_response(error_message: str) -> dict:
    """Create standardized error response."""
    return {
        "error": error_message,
        "success": False
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="analyze_video_metadata",
            description="分析视频文件的元信息和编码参数，包括容器格式、编码器、分辨率、帧率等",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "视频文件路径"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="analyze_gop_structure",
            description="分析视频的 GOP 结构和帧类型分布，包括 I/P/B 帧统计和关键帧时间戳",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "视频文件路径"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="compare_quality_metrics",
            description="对比两个视频文件的画质指标，包括 PSNR、SSIM 和 VMAF",
            inputSchema={
                "type": "object",
                "properties": {
                    "reference": {
                        "type": "string",
                        "description": "参考视频路径"
                    },
                    "distorted": {
                        "type": "string",
                        "description": "待评估视频路径"
                    }
                },
                "required": ["reference", "distorted"]
            }
        ),
        Tool(
            name="analyze_artifacts",
            description="分析视频伪影和主观质量代理指标。可进行单流分析或转码前后对比分析",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "目标视频路径"
                    },
                    "reference": {
                        "type": "string",
                        "description": "参考视频路径（可选，提供时进行对比分析）"
                    }
                },
                "required": ["target"]
            }
        ),
        Tool(
            name="summarize_transcode_comparison",
            description="生成转码效果的综合评估报告，包括质量变化、关键问题和优化建议",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "源视频路径"
                    },
                    "transcoded": {
                        "type": "string",
                        "description": "转码后视频路径"
                    }
                },
                "required": ["source", "transcoded"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        if name == "analyze_video_metadata":
            path = arguments.get("path")
            if not path:
                return [TextContent(
                    type="text",
                    text=json.dumps(create_error_response("Missing required parameter: path"), ensure_ascii=False)
                )]
            
            result = analyze_video_metadata(path)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "analyze_gop_structure":
            path = arguments.get("path")
            if not path:
                return [TextContent(
                    type="text",
                    text=json.dumps(create_error_response("Missing required parameter: path"), ensure_ascii=False)
                )]
            
            result = analyze_gop_structure(path)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "compare_quality_metrics":
            reference = arguments.get("reference")
            distorted = arguments.get("distorted")
            
            if not reference:
                return [TextContent(
                    type="text",
                    text=json.dumps(create_error_response("Missing required parameter: reference"), ensure_ascii=False)
                )]
            if not distorted:
                return [TextContent(
                    type="text",
                    text=json.dumps(create_error_response("Missing required parameter: distorted"), ensure_ascii=False)
                )]
            
            result = compare_quality_metrics(reference, distorted)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "analyze_artifacts":
            target = arguments.get("target")
            reference = arguments.get("reference")
            
            if not target:
                return [TextContent(
                    type="text",
                    text=json.dumps(create_error_response("Missing required parameter: target"), ensure_ascii=False)
                )]
            
            result = analyze_artifacts(target, reference)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "summarize_transcode_comparison":
            source = arguments.get("source")
            transcoded = arguments.get("transcoded")
            
            if not source:
                return [TextContent(
                    type="text",
                    text=json.dumps(create_error_response("Missing required parameter: source"), ensure_ascii=False)
                )]
            if not transcoded:
                return [TextContent(
                    type="text",
                    text=json.dumps(create_error_response("Missing required parameter: transcoded"), ensure_ascii=False)
                )]
            
            result = summarize_transcode_comparison(source, transcoded)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps(create_error_response(f"Unknown tool: {name}"), ensure_ascii=False)
            )]
    
    except FFmpegError as e:
        return [TextContent(
            type="text",
            text=json.dumps(create_error_response(str(e)), ensure_ascii=False)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps(create_error_response(f"Unexpected error: {str(e)}"), ensure_ascii=False)
        )]


async def run_server():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


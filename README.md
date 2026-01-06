# Video Quality MCP Server

An MCP (Model Context Protocol) Server for video quality analysis and transcoding effect comparison.

## Features

- 📹 **Video Metadata Analysis** - Extract encoding parameters, resolution, frame rate, etc.
- 🎬 **GOP/Frame Structure Analysis** - Analyze keyframe distribution and GOP structure
- 📊 **Quality Metrics Comparison** - Calculate objective metrics like PSNR, SSIM, VMAF
- 🔍 **Artifact Analysis** - Detect blur, blocking, ringing, banding, dark detail loss
- 📝 **Transcode Summary** - Generate LLM-friendly transcoding quality assessment reports

## Installation

```bash
pip install -r requirements.txt
```

## Running

### Running as MCP Server

```bash
python main.py
```

The server communicates with clients via stdio protocol.

### Configuration in Cursor

Add the following to your Cursor MCP configuration file:

```json
{
  "mcpServers": {
    "video-quality": {
      "command": "python",
      "args": ["/path/to/video-quality-mcp/main.py"]
    }
  }
}
```

## Tools

### 1. analyze_video_metadata

Parse video file metadata and encoding parameters.

**Input:**
- `path` (string): Path to video file

**Output:**
- Container format, duration, file size, bitrate
- Video codec, profile, level, resolution, frame rate, pixel format

### 2. analyze_gop_structure

Analyze video GOP structure and frame type distribution.

**Input:**
- `path` (string): Path to video file

**Output:**
- I/P/B frame distribution statistics
- GOP average/min/max length
- Keyframe timestamp list

### 3. compare_quality_metrics

Compare quality metrics between two video files.

**Input:**
- `reference` (string): Path to reference video
- `distorted` (string): Path to video to evaluate

**Output:**
- PSNR (Y/U/V components)
- SSIM score
- VMAF score

### 4. analyze_artifacts

Analyze video artifacts and perceptual quality proxy metrics.

**Input:**
- `target` (string): Path to target video
- `reference` (string, optional): Path to reference video (optional)

**Output:**
- Single stream mode: Artifact type scores
- Comparison mode: Artifact change delta values
- Risk summary and likely causes

### 5. summarize_transcode_comparison

Generate comprehensive transcoding effect assessment report.

**Input:**
- `source` (string): Path to source video
- `transcoded` (string): Path to transcoded video

**Output:**
- Quality change verdict
- VMAF delta and bitrate savings
- Key issues list
- Encoding parameter optimization recommendations

## Technical Implementation

- **FFmpeg/ffprobe Wrapper** - Unified command-line interface
- **No Deep Learning Dependencies** - Uses traditional image processing and signal analysis methods
- **Structured Output** - All tools return standard JSON format
- **Error Handling** - Clear error message return mechanism

## Requirements

- Python 3.10+
- FFmpeg (must be installed and configured in PATH)
- Python packages listed in `requirements.txt`

## Notes

- Ensure FFmpeg is properly installed with VMAF support
- Large file analysis may take a long time
- All paths should preferably use absolute paths

## Documentation

For Chinese documentation, see [README.zh.md](README.zh.md).

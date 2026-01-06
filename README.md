# Video Quality MCP Server

An MCP (Model Context Protocol) Server for video quality analysis and transcoding effect comparison.

一个用于视频画质分析与转码效果对比的 MCP (Model Context Protocol) Server。

## Features / 功能特性

- 📹 **Video Metadata Analysis** / **视频元信息解析** - Extract encoding parameters, resolution, frame rate, etc.
- 🎬 **GOP/Frame Structure Analysis** / **GOP/帧结构分析** - Analyze keyframe distribution and GOP structure
- 📊 **Quality Metrics Comparison** / **画质指标对比** - Calculate objective metrics like PSNR, SSIM, VMAF
- 🔍 **Artifact Analysis** / **伪影分析** - Detect blur, blocking, ringing, banding, dark detail loss
- 📝 **Transcode Summary** / **转码效果总结** - Generate LLM-friendly transcoding quality assessment reports

## Installation / 安装依赖

```bash
pip install -r requirements.txt
```

## Running / 运行方式

### Running as MCP Server / 作为 MCP Server 运行

```bash
python main.py
```

The server communicates with clients via stdio protocol.

Server 将通过 stdio 协议与客户端通信。

### Configuration in Cursor / 在 Cursor 中配置

Add the following to your Cursor MCP configuration file:

在 Cursor 的 MCP 配置文件中添加：

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

## Tools / 工具说明

### 1. analyze_video_metadata

Parse video file metadata and encoding parameters.

解析视频文件的元信息和编码参数。

**Input / 输入：**
- `path` (string): Path to video file / 视频文件路径

**Output / 输出：**
- Container format, duration, file size, bitrate / 容器格式、时长、文件大小、码率
- Video codec, profile, level, resolution, frame rate, pixel format / 视频编码器、profile、level、分辨率、帧率、像素格式

### 2. analyze_gop_structure

Analyze video GOP structure and frame type distribution.

分析视频的 GOP 结构和帧类型分布。

**Input / 输入：**
- `path` (string): Path to video file / 视频文件路径

**Output / 输出：**
- I/P/B frame distribution statistics / I/P/B 帧分布统计
- GOP average/min/max length / GOP 平均/最小/最大长度
- Keyframe timestamp list / 关键帧时间戳列表

### 3. compare_quality_metrics

Compare quality metrics between two video files.

对比两个视频文件的画质指标。

**Input / 输入：**
- `reference` (string): Path to reference video / 参考视频路径
- `distorted` (string): Path to video to evaluate / 待评估视频路径

**Output / 输出：**
- PSNR (Y/U/V components) / PSNR (Y/U/V 分量)
- SSIM score / SSIM 分数
- VMAF score / VMAF 分数

### 4. analyze_artifacts

Analyze video artifacts and perceptual quality proxy metrics.

分析视频伪影和主观质量代理指标。

**Input / 输入：**
- `target` (string): Path to target video / 目标视频路径
- `reference` (string, optional): Path to reference video (optional) / 参考视频路径（可选）

**Output / 输出：**
- Single stream mode: Artifact type scores / 单流模式：各伪影类型评分
- Comparison mode: Artifact change delta values / 对比模式：伪影变化 delta 值
- Risk summary and likely causes / 风险总结与可能原因

### 5. summarize_transcode_comparison

Generate comprehensive transcoding effect assessment report.

生成转码效果的综合评估报告。

**Input / 输入：**
- `source` (string): Path to source video / 源视频路径
- `transcoded` (string): Path to transcoded video / 转码后视频路径

**Output / 输出：**
- Quality change verdict / 质量变化 verdict
- VMAF delta and bitrate savings / VMAF delta 和码率节省
- Key issues list / 关键问题列表
- Encoding parameter optimization recommendations / 编码参数优化建议

## Technical Implementation / 技术实现

- **FFmpeg/ffprobe Wrapper** / **FFmpeg/ffprobe 封装** - Unified command-line interface / 统一的命令行调用接口
- **No Deep Learning Dependencies** / **无深度学习依赖** - Uses traditional image processing and signal analysis methods / 使用传统图像处理与信号分析方法
- **Structured Output** / **结构化输出** - All tools return standard JSON format / 所有工具返回标准 JSON 格式
- **Error Handling** / **错误处理** - Clear error message return mechanism / 明确的错误信息返回机制

## Requirements / 依赖要求

- Python 3.10+
- FFmpeg (must be installed and configured in PATH) / FFmpeg (需安装并配置在 PATH 中)
- Python packages listed in `requirements.txt` / 相关 Python 包见 `requirements.txt`

## Notes / 注意事项

- Ensure FFmpeg is properly installed with VMAF support / 确保 FFmpeg 已正确安装并包含 VMAF 支持
- Large file analysis may take a long time / 大文件分析可能需要较长时间
- All paths should preferably use absolute paths / 所有路径建议使用绝对路径

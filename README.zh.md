# Video Quality MCP Server

一个用于视频画质分析与转码效果对比的 MCP (Model Context Protocol) Server。

## 功能特性

- 📹 **视频元信息解析** - 提取编码参数、分辨率、帧率等
- 🎬 **GOP/帧结构分析** - 分析关键帧分布与 GOP 结构
- 📊 **画质指标对比** - 计算 PSNR、SSIM、VMAF 等客观指标
- 🔍 **伪影分析** - 检测模糊、块效应、振铃、色带、暗部细节丢失
- 📝 **转码效果总结** - 生成 LLM 友好的转码质量评估报告

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行方式

### 作为 MCP Server 运行

```bash
python main.py
```

Server 将通过 stdio 协议与客户端通信。

### 在 Cursor 中配置

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

## 工具说明

### 1. analyze_video_metadata

解析视频文件的元信息和编码参数。

**输入：**
- `path` (string): 视频文件路径

**输出：**
- 容器格式、时长、文件大小、码率
- 视频编码器、profile、level、分辨率、帧率、像素格式

### 2. analyze_gop_structure

分析视频的 GOP 结构和帧类型分布。

**输入：**
- `path` (string): 视频文件路径

**输出：**
- I/P/B 帧分布统计
- GOP 平均/最小/最大长度
- 关键帧时间戳列表

### 3. compare_quality_metrics

对比两个视频文件的画质指标。

**输入：**
- `reference` (string): 参考视频路径
- `distorted` (string): 待评估视频路径

**输出：**
- PSNR (Y/U/V 分量)
- SSIM 分数
- VMAF 分数

### 4. analyze_artifacts

分析视频伪影和主观质量代理指标。

**输入：**
- `target` (string): 目标视频路径
- `reference` (string, optional): 参考视频路径（可选）

**输出：**
- 单流模式：各伪影类型评分
- 对比模式：伪影变化 delta 值
- 风险总结与可能原因

### 5. summarize_transcode_comparison

生成转码效果的综合评估报告。

**输入：**
- `source` (string): 源视频路径
- `transcoded` (string): 转码后视频路径

**输出：**
- 质量变化 verdict
- VMAF delta 和码率节省
- 关键问题列表
- 编码参数优化建议

## 技术实现

- **FFmpeg/ffprobe 封装** - 统一的命令行调用接口
- **无深度学习依赖** - 使用传统图像处理与信号分析方法
- **结构化输出** - 所有工具返回标准 JSON 格式
- **错误处理** - 明确的错误信息返回机制

## 依赖要求

- Python 3.10+
- FFmpeg (需安装并配置在 PATH 中)
- 相关 Python 包见 `requirements.txt`

## 注意事项

- 确保 FFmpeg 已正确安装并包含 VMAF 支持
- 大文件分析可能需要较长时间
- 所有路径建议使用绝对路径

## 文档

英文文档请参见 [README.md](README.md)。


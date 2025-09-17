# RTX 2080 Ti Optimization Guide

This guide covers the specific optimizations implemented for RTX 2080 Ti (11GB VRAM) based on the problem statement requirements.

## System Requirements

- **GPU**: RTX 2080 Ti (11GB VRAM)
- **CPU**: i9-9900KS (12 cores recommended)
- **RAM**: 32GB+ recommended
- **Storage**: SSD for model files and cache

## Key Optimizations Implemented

### 1. LLM Engine Optimizations (`orchestrator/llm_engine.py`)

#### Memory Management
- **Q4_K_M quantization** for 14B models (~8.5GB)
- **1-2GB VRAM headroom** maintained automatically
- **KV cache quantization** (Q8_0/Q4_0) reduces memory pressure
- **Context length**: 8K tokens (expandable to 32K with RoPE)

#### Performance Features
- **Speculative decoding** with prompt lookup (1.5-2x speedup)
- **Flash attention** for GPU acceleration
- **KQV offload** keeps matrix operations on GPU
- **Optimal batch sizes**: 1024 prefill, 256 decode
- **Prompt caching** for repeated system messages

#### Generation Quality
- **GBNF grammar** for bulletproof structured outputs
- **Deterministic generation** (seed=42, temp=0.2-0.4)
- **Automatic retry** with temperature adjustment
- **Schema validation** with Pydantic

### 2. Performance Tuning (`orchestrator/perf.py`)

#### Automatic Configuration
- **RTX 2080 Ti specific profiles** with memory constraints
- **Batch size optimization** (256-2048 range)
- **KV quantization testing** (Q4_0, Q8_0, F16)
- **VRAM usage validation** with 11GB limit

#### Benchmarking
- **Mock performance testing** for configuration validation
- **Real-time tok/s measurement** during generation
- **Memory usage tracking** (GPU and system RAM)
- **Recommendation engine** for optimal settings

### 3. NVENC Rendering (`orchestrator/render.py`)

#### Hardware Acceleration
- **H.264 NVENC** optimized for RTX 2080 Ti
- **Preset P4-P5** for speed/quality balance
- **Spatial/temporal adaptive quantization**
- **B-frame reference mode** optimization
- **Rate control lookahead** (20 frames)

#### Audio Processing
- **EBU R128 loudness normalization**
  - Integrated loudness: -16 LUFS
  - True peak limit: -1.5 dBTP
  - Loudness range: 11 LU
- **Crossfade transitions** with complex filter graphs
- **Stream validation** for concat compatibility

### 4. Configuration (`orchestrator/config.toml`)

```toml
[llm]
model_path = "models/Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf"
n_ctx = 8192              # 8K context, expandable
n_batch = 1024            # Optimal for 2080 Ti
n_ubatch = 256            # Decode microbatch
n_threads = 12            # Physical cores
flash_attn = true         # GPU acceleration
offload_kqv = true        # Keep operations on GPU
enable_speculative_decoding = true
type_k = "Q8_0"           # KV cache quantization
type_v = "Q8_0"

[ffmpeg]
output_codec = "h264_nvenc"
preset = "p4"             # RTX 2080 Ti optimized
audio_normalize = true    # EBU R128 standards
```

## Performance Targets

### Expected Throughput
- **Baseline**: 14B model typically achieves 10-25 tok/s
- **With optimizations**: 30-40 tok/s target
- **Speculative decoding**: 1.5-2x improvement
- **Memory usage**: 9-10GB VRAM (1-2GB headroom)

### Quality Assurance
- **WCAG AA compliance**: 4.5:1 contrast ratio
- **Okabe-Ito color palette** for accessibility
- **Geometric validation** (overlap detection)
- **Audio standards** (EBU R128 loudness)

## Installation & Setup

### 1. Dependencies
```bash
pip install llama-cpp-python[server] toml pydantic psutil GPUtil
pip install manim ffmpeg-python  # Optional but recommended
```

### 2. CUDA Setup
- Install NVIDIA driver compatible with RTX 2080 Ti
- Install CUDA toolkit for cuBLAS support
- Set power management to "Prefer maximum performance"
- Enable GPU scheduling (Windows) or persistence mode (Linux)

### 3. Model Download
```bash
# Primary model (Q4_K_M for optimal VRAM usage)
cd models/
wget https://huggingface.co/bartowski/Qwen2.5-Coder-14B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf

# Optional: Draft model for speculative decoding
wget https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-1.5B-Instruct-Q8_0.gguf
```

## Usage

### 1. System Validation
```bash
python setup_enhanced_system.py
```

### 2. Performance Tuning
```bash
python orchestrator/perf.py --advanced-tune
```

### 3. Full Pipeline
```bash
python orchestrator/run.py --topic "quantum mechanics" --duration 15
```

### 4. Demo System
```bash
python demo_enhanced_system.py
```

## Troubleshooting

### Performance Issues
- Check VRAM usage with `nvidia-smi`
- Reduce batch size if getting OOM errors
- Try more aggressive quantization (Q4_0)
- Ensure GPU persistence mode is enabled

### Quality Issues
- Increase context length for complex topics
- Adjust temperature for more/less creativity
- Enable GBNF grammar for structured outputs
- Use retry logic for failed generations

### Rendering Issues
- Verify NVENC availability with `ffmpeg -encoders | grep nvenc`
- Check stream compatibility with validation
- Monitor encoding preset performance
- Ensure adequate storage space for outputs

## Advanced Features

### Speculative Decoding
- **Prompt lookup**: No additional model needed
- **Draft model**: Requires separate small model
- **Token prediction**: 2-4 tokens ahead
- **Verification**: Main model validates drafts

### GBNF Grammar
- **Schema enforcement**: Guarantees valid JSON
- **API constraints**: Prevents hallucinated calls
- **Structured outputs**: Reliable parsing
- **Grammar compilation**: From Pydantic schemas

### Professional Audio
- **Loudness standards**: EBU R128 compliance
- **Dynamic range**: Consistent across segments
- **Peak limiting**: Prevents distortion
- **Broadcast ready**: Professional quality

## Best Practices

### Memory Management
1. Monitor VRAM usage continuously
2. Leave 1-2GB headroom for stability
3. Use appropriate quantization levels
4. Clear cache periodically for long sessions

### Performance Optimization
1. Profile before production deployment
2. Test different batch size combinations
3. Monitor thermal throttling under load
4. Use dedicated GPU without display load

### Quality Control
1. Validate all generated code with AST
2. Check geometric constraints automatically
3. Verify audio levels meet broadcast standards
4. Test edge cases with retry logic

This optimization guide ensures maximum performance and reliability for RTX 2080 Ti deployments while maintaining professional quality standards.
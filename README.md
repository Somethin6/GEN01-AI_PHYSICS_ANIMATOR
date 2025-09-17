# AI Physics Animator

A bulletproof AI-powered physics animation system using in-process Llama.cpp and Manim Community. 
Designed for high performance on GPUs like the RTX 2080 Ti.

## Features

- **In-process LLM**: No HTTP overhead, direct Llama.cpp integration with CUDA acceleration
- **Structured Pipeline**: 6-layer validation with JSON schemas and "doctors"
- **RAG Knowledge Base**: ~150 Manim code snippets with semantic search
- **Visual Critic**: Geometry-based analysis using Manim APIs (no computer vision)
- **Beat-by-beat Rendering**: Scalable video composition with FFmpeg concat
- **Performance Optimized**: GPU offload, flash attention, KV cache quantization

## Architecture

```
Concept → Understanding → Outline → Derivation → VideoOutline → Codegen → Doctor → Critic → Repair → Render → Compose
```

Each layer has:
- **Agent**: Generates structured output using LLM
- **Doctor**: Validates output with strict rules  
- **Schema**: Pydantic type enforcement

## Installation

### 1. System Requirements

- Python 3.8+
- CUDA-compatible GPU (tested on RTX 2080 Ti)
- Manim Community v0.19.0+
- FFmpeg

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install llama-cpp-python with CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python[server] --force-reinstall --no-cache-dir
```

### 3. Download Model

Download a GGUF model (e.g., Qwen2.5-14B-Instruct) to `models/`:

```bash
mkdir -p models
# Download your preferred GGUF model
# Example: wget https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q5_k_m.gguf -P models/
```

### 4. Verify Installation

```bash
# Test Manim
manim --version

# Test FFmpeg  
ffmpeg -version

# Test the system
python orchestrator/run.py --topic "simple harmonic motion" --duration 10
```

## Usage

### Basic Usage

```bash
python orchestrator/run.py --topic "wave interference patterns" --duration 15
```

### Performance Tuning

```bash
# Benchmark current configuration
python orchestrator/perf.py --benchmark

# Auto-tune for optimal performance
python orchestrator/perf.py --auto-tune

# Full configuration sweep
python orchestrator/perf.py --sweep
```

### Advanced Usage

```bash
# Resume from checkpoint
python orchestrator/run.py --topic "quantum mechanics" --duration 20

# Reset state and start fresh
python orchestrator/run.py --topic "electromagnetism" --reset

# Custom configuration
python orchestrator/run.py --topic "thermodynamics" --config custom_config.toml
```

## Configuration

Edit `orchestrator/config.toml` to customize:

- **LLM settings**: Model path, GPU layers, batch size, KV quantization
- **Performance**: Target tok/s, memory limits
- **Quality**: Manim resolution, FFmpeg encoding
- **RAG**: Embedding model, similarity thresholds

## Project Structure

```
ai-video/
├── models/                 # GGUF model files
├── kb/                     # Manim knowledge base + embeddings
├── orchestrator/           # Core system
│   ├── config.toml        # Configuration
│   ├── schemas.py         # Pydantic schemas
│   ├── llm_engine.py      # In-process Llama.cpp
│   ├── rag.py             # Knowledge base & retrieval
│   ├── agents.py          # Pipeline agents
│   ├── doctors.py         # Validation doctors
│   ├── critic.py          # Visual analysis
│   ├── render.py          # Manim & FFmpeg
│   ├── perf.py            # Performance tuning
│   └── run.py             # Main orchestrator
├── manim_project/         # Generated scenes
│   ├── scenes/            # Per-beat Python files
│   └── out/               # Per-beat MP4s
└── compose/               # Final composition
    ├── lists/             # FFmpeg concat lists
    └── out/               # Final videos
```

## Performance Optimization

### GPU Configuration

For RTX 2080 Ti (8GB VRAM):

```toml
[llm]
n_gpu_layers = -1          # Offload all layers
n_batch = 1024             # Large batch for throughput
n_ubatch = 512             # Decode batch size
flash_attn = true          # Flash attention
type_k = "Q8_0"           # KV cache quantization
type_v = "Q8_0"           
```

### System Tuning

**Windows (WDDM)**:
- Close GPU-heavy applications
- Use dedicated GPU mode in Windows settings

**Linux**:
```bash
# Set exclusive compute mode
sudo nvidia-smi -c EXCLUSIVE_PROCESS
```

## Troubleshooting

### Common Issues

**Low tok/s performance**:
- Check CUDA installation: `nvidia-smi`
- Verify llama-cpp-python built with CUDA: `python -c "import llama_cpp; print(llama_cpp.__version__)"`
- Run performance tuning: `python orchestrator/perf.py --auto-tune`

**Out of VRAM**:
- Reduce `n_batch` in config
- Enable aggressive KV quantization: `type_k = "Q4_0"`
- Use smaller model or lower quantization

**Manim render errors**:
- Check Manim installation: `manim --version`
- Verify LaTeX installation for math rendering
- Check generated scene files in `manim_project/scenes/`

**FFmpeg composition fails**:
- Verify FFmpeg installation: `ffmpeg -version`
- Check beat files exist in `manim_project/out/`
- Ensure all beats have matching video parameters

### Debug Mode

Enable verbose logging:

```bash
export MANIM_VERBOSITY=DEBUG
python orchestrator/run.py --topic "your topic"
```

## Performance Benchmarks

Target performance on RTX 2080 Ti:
- **Inference**: 30+ tok/s with 14B model
- **Beat rendering**: 30-60s per beat
- **Final composition**: <30s for 15s video

Actual performance depends on:
- Model size and quantization
- Scene complexity
- System configuration

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all existing tests pass
5. Submit pull request

## License

MIT License - see LICENSE file for details.

## Citation

If you use this system in research, please cite:

```bibtex
@software{ai_physics_animator,
  title={AI Physics Animator: In-Process LLM-Driven Educational Video Generation},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/ai-physics-animator}
}
```
# AI Physics Animator (GEN01)

> **Archived predecessor / experimental generation.** This repository captures an earlier iteration of the physics-video project that later evolved into **Physics Foundry**. It is retained for development history and selected implementation ideas, not as the current flagship system.

GEN01 explored a local LLM-driven pipeline for generating Manim-based physics animations with structured intermediate representations, validation layers, retrieval from a small code knowledge base, rendering, and FFmpeg composition.

## Historical architecture

```text
Concept
  ↓
Understanding
  ↓
Outline
  ↓
Derivation
  ↓
Video outline
  ↓
Code generation
  ↓
Validation / repair
  ↓
Manim render
  ↓
Composition
```

The project experimented with:

- llama.cpp / local GGUF inference
- Pydantic-structured pipeline stages
- retrieval of Manim examples/snippets
- generated-code validation and repair loops
- Manim scene generation
- FFmpeg composition
- hardware/performance configuration for local GPU inference

## Status and limitations

This generation should **not** be interpreted as a finished, production-grade autonomous animation system.

- performance figures in older documentation were targets/configuration assumptions rather than universally reproduced benchmarks
- model, CUDA, Manim, FFmpeg, and LaTeX dependencies are environment-specific
- generated-code correctness and physics correctness require separate validation
- several ideas from this prototype were superseded by the more modular orchestration architecture in Physics Foundry

## Current project

The active public successor is:

**Physics Foundry**  
https://github.com/ddelucchi/physics-video-genera

Physics Foundry is the repository intended for current development and portfolio review. GEN01 remains available to preserve the earlier design lineage and experiments.

## Why keep this repository?

The repository documents an earlier architectural approach centered on an in-process local LLM, structured validation stages, Manim generation, and local composition. Keeping it separate preserves technical history while avoiding confusion about which implementation is current.

## License

See [LICENSE](LICENSE).

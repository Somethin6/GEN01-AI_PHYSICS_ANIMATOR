#!/usr/bin/env python3
"""
Setup and validation script for AI Physics Animator enhancements.
Verifies installation and runs basic tests.
"""

import sys
import importlib
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    print("=" * 40)
    
    required_packages = [
        ("toml", "Configuration parsing"),
        ("pydantic", "Data validation"),
        ("llama_cpp", "LLM inference"),
        ("numpy", "Numerical computing"),
        ("pathlib", "Path handling"),
    ]
    
    optional_packages = [
        ("manim", "Animation rendering"),
        ("ffmpeg", "Video processing"),
        ("chromadb", "Vector database"),
        ("sentence_transformers", "Embeddings"),
    ]
    
    missing_required = []
    missing_optional = []
    
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package:<20} - {description}")
        except ImportError:
            print(f"❌ {package:<20} - {description} (REQUIRED)")
            missing_required.append(package)
    
    for package, description in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package:<20} - {description}")
        except ImportError:
            print(f"⚠️  {package:<20} - {description} (optional)")
            missing_optional.append(package)
    
    print(f"\n📊 Status: {len(required_packages) - len(missing_required)}/{len(required_packages)} required packages installed")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("Install with: pip install " + " ".join(missing_optional))
    
    return True


def check_configuration():
    """Check configuration files"""
    print("\n🔧 Checking Configuration...")
    print("=" * 40)
    
    config_file = Path("orchestrator/config.toml")
    
    if not config_file.exists():
        print("❌ Configuration file not found: orchestrator/config.toml")
        return False
    
    try:
        import toml
        config = toml.load(config_file)
        
        required_sections = ["llm", "performance", "ffmpeg", "orchestrator"]
        for section in required_sections:
            if section in config:
                print(f"✅ Configuration section: {section}")
            else:
                print(f"❌ Missing configuration section: {section}")
                return False
        
        # Check LLM optimizations
        llm_config = config["llm"]
        optimizations = [
            ("flash_attn", "Flash attention"),
            ("offload_kqv", "KV offload"),
            ("enable_speculative_decoding", "Speculative decoding"),
        ]
        
        print("\n🚀 LLM Optimizations:")
        for key, desc in optimizations:
            if llm_config.get(key, False):
                print(f"✅ {desc} enabled")
            else:
                print(f"⚠️  {desc} disabled")
        
        # Check NVENC settings
        ffmpeg_config = config["ffmpeg"]
        if ffmpeg_config.get("output_codec") == "h264_nvenc":
            print("✅ NVENC acceleration enabled")
        else:
            print("⚠️  NVENC acceleration not configured")
        
        if ffmpeg_config.get("audio_normalize", False):
            print("✅ Audio loudness normalization enabled")
        else:
            print("⚠️  Audio loudness normalization disabled")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def check_directories():
    """Check required directories"""
    print("\n📁 Checking Directories...")
    print("=" * 40)
    
    required_dirs = [
        "orchestrator",
        "models",
    ]
    
    optional_dirs = [
        "manim_project",
        "compose",
        "kb",
    ]
    
    for directory in required_dirs:
        dir_path = Path(directory)
        if dir_path.exists():
            print(f"✅ {directory}/ exists")
        else:
            print(f"❌ {directory}/ missing (REQUIRED)")
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   Created {directory}/")
    
    for directory in optional_dirs:
        dir_path = Path(directory)
        if dir_path.exists():
            print(f"✅ {directory}/ exists")
        else:
            print(f"⚠️  {directory}/ missing (will be created on demand)")
    
    # Check models directory content
    models_dir = Path("models")
    if models_dir.exists():
        gguf_files = list(models_dir.glob("*.gguf"))
        if gguf_files:
            print(f"✅ Found {len(gguf_files)} GGUF model(s)")
            for model in gguf_files:
                print(f"   - {model.name}")
        else:
            print("⚠️  No GGUF models found in models/ directory")
            print("   Download models to enable full functionality")
    
    return True


def test_llm_engine():
    """Test LLM engine initialization"""
    print("\n🧠 Testing LLM Engine...")
    print("=" * 40)
    
    try:
        from orchestrator.llm_engine import LLMEngine
        
        # Test configuration loading
        try:
            engine = LLMEngine("orchestrator/config.toml")
            print("❌ LLM engine loaded (unexpected - no model file)")
        except FileNotFoundError as e:
            if "Model not found" in str(e):
                print("✅ LLM engine correctly handles missing model")
            else:
                print(f"❌ Unexpected error: {e}")
        
        # Test VRAM estimation
        try:
            import toml
            config = toml.load("orchestrator/config.toml")
            
            # Mock engine for estimation
            engine = LLMEngine.__new__(LLMEngine)
            engine.config = config["llm"]
            
            estimation = engine.estimate_vram_usage()
            print("✅ VRAM estimation working")
            print(f"   Estimated model size: {estimation['model_gb']:.1f}GB")
            print(f"   Estimated total usage: {estimation['total_estimated_mb']:.0f}MB")
            print(f"   Estimated headroom: {estimation['headroom_mb']:.0f}MB")
            
        except Exception as e:
            print(f"❌ VRAM estimation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM engine test failed: {e}")
        return False


def test_performance_tuner():
    """Test performance tuner"""
    print("\n⚡ Testing Performance Tuner...")
    print("=" * 40)
    
    try:
        from orchestrator.perf import PerformanceTuner
        
        tuner = PerformanceTuner("orchestrator/config.toml")
        print("✅ Performance tuner initialized")
        
        # Test mock benchmark
        test_config = {
            "name": "Test Config",
            "n_batch": 512,
            "n_ubatch": 256,
            "type_k": "Q8_0",
            "flash_attn": True,
            "offload_kqv": True
        }
        
        result = tuner._run_advanced_mock_benchmark(test_config)
        print("✅ Mock benchmark working")
        print(f"   Simulated performance: {result.tokens_per_second:.1f} tok/s")
        print(f"   Simulated VRAM usage: {result.gpu_memory_mb:.0f}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tuner test failed: {e}")
        return False


def test_render_system():
    """Test rendering system"""
    print("\n🎬 Testing Render System...")
    print("=" * 40)
    
    try:
        from orchestrator.render import VideoComposer
        
        composer = VideoComposer("orchestrator/config.toml")
        print("✅ Video composer initialized")
        print(f"   NVENC codec: {composer.config['output_codec']}")
        print(f"   Preset: {composer.config['preset']}")
        print(f"   Audio normalization: {composer.config.get('audio_normalize', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Render system test failed: {e}")
        return False


def main():
    """Main setup and validation"""
    print("🚀 AI Physics Animator - Enhanced System Setup")
    print("=" * 60)
    
    success = True
    
    # Check dependencies
    if not check_dependencies():
        success = False
    
    # Check configuration
    if not check_configuration():
        success = False
    
    # Check directories
    if not check_directories():
        success = False
    
    # Test components
    if not test_llm_engine():
        success = False
    
    if not test_performance_tuner():
        success = False
    
    if not test_render_system():
        success = False
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 System validation completed successfully!")
        print("\n✅ Ready for enhanced video generation with:")
        print("   • Optimized LLM inference with speculative decoding")
        print("   • NVENC hardware acceleration for RTX 2080 Ti")
        print("   • Audio loudness normalization (EBU R128)")
        print("   • Performance tuning and monitoring")
        print("   • Enhanced error handling and retry logic")
        
        print("\n📝 Next steps:")
        print("   1. Download GGUF models to ./models/ directory")
        print("   2. Run: python orchestrator/perf.py --advanced-tune")
        print("   3. Test full pipeline: python orchestrator/run.py --topic 'quantum mechanics'")
        
    else:
        print("❌ System validation found issues")
        print("   Please resolve the errors above before proceeding")
    
    return success


if __name__ == "__main__":
    main()
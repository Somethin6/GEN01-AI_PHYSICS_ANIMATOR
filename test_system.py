#!/usr/bin/env python3
"""
Test script to verify the AI Physics Animator system components.
Tests each component individually before full integration.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))

def test_imports():
    """Test that all required components can be imported"""
    print("Testing imports...")
    
    try:
        import toml
        import pydantic
        import numpy as np
        print("✓ Basic dependencies imported")
    except ImportError as e:
        print(f"✗ Missing basic dependency: {e}")
        return False
    
    try:
        from orchestrator.schemas import ConceptSchema, ValidationResult
        print("✓ Schemas imported")
    except ImportError as e:
        print(f"✗ Failed to import schemas: {e}")
        return False
    
    try:
        # Test llama-cpp-python import
        import llama_cpp
        print("✓ llama-cpp-python imported")
    except ImportError as e:
        print(f"✗ llama-cpp-python not available: {e}")
        print("  Install with: pip install llama-cpp-python[server]")
        return False
    
    try:
        import manim
        print("✓ Manim imported")
    except ImportError as e:
        print(f"✗ Manim not available: {e}")
        print("  Install with: pip install manim")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    config_path = Path("orchestrator/config.toml")
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        return False
    
    try:
        import toml
        config = toml.load(config_path)
        
        required_sections = ["llm", "performance", "manim", "rag", "critic", "ffmpeg", "orchestrator"]
        for section in required_sections:
            if section not in config:
                print(f"✗ Missing config section: {section}")
                return False
        
        print("✓ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False

def test_schemas():
    """Test Pydantic schema validation"""
    print("\nTesting schemas...")
    
    try:
        from orchestrator.schemas import ConceptSchema, ValidationResult
        
        # Test valid concept
        concept_data = {
            "topic": "Simple Harmonic Motion",
            "audience": "undergraduate",
            "target_duration_sec": 15.0,
            "thesis": "Simple harmonic motion is characterized by restoring force proportional to displacement",
            "scope": ["spring oscillations", "pendulum motion", "energy conservation"],
            "prerequisites": ["basic calculus", "Newton's laws"],
            "risks": ["confusing frequency with period"],
            "sources": ["Halliday & Resnick Physics"]
        }
        
        # Test with appropriate Pydantic method based on version
        try:
            concept = ConceptSchema.model_validate(concept_data)  # Pydantic v2
        except AttributeError:
            concept = ConceptSchema.parse_obj(concept_data)  # Pydantic v1
        print("✓ ConceptSchema validation works")
        
        # Test validation result
        result = ValidationResult(valid=True, errors=[], warnings=["test warning"])
        print("✓ ValidationResult schema works")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        return False

def test_knowledge_base():
    """Test knowledge base initialization"""
    print("\nTesting knowledge base...")
    
    try:
        from orchestrator.rag import ManimKnowledgeBase
        
        # Create temporary config for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
[rag]
embedding_model = "all-MiniLM-L6-v2"
chunk_size = 512
chunk_overlap = 50
top_k = 5
min_similarity = 0.7
""")
            temp_config = f.name
        
        try:
            kb = ManimKnowledgeBase(temp_config)
            
            # Test retrieval
            results = kb.retrieve("text animation")
            if results:
                print(f"✓ Knowledge base retrieval works ({len(results)} results)")
            else:
                print("⚠ Knowledge base retrieval returned no results")
            
            # Test snippet access
            snippets = kb.get_all_snippets()
            if len(snippets) > 0:
                print(f"✓ Knowledge base has {len(snippets)} snippets")
            else:
                print("⚠ Knowledge base has no snippets")
            
            return True
            
        finally:
            os.unlink(temp_config)
            
    except ImportError as e:
        print(f"✗ Missing dependency for knowledge base: {e}")
        print("  Install with: pip install sentence-transformers faiss-cpu")
        return False
    except Exception as e:
        print(f"✗ Knowledge base test failed: {e}")
        return False

def test_manim_health():
    """Test Manim installation"""
    print("\nTesting Manim...")
    
    try:
        import subprocess
        
        # Check manim command
        result = subprocess.run(["manim", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Manim installed: {version}")
        else:
            print("✗ Manim command failed")
            return False
        
        # Test basic scene compilation
        test_scene = '''
from manim import *

class TestScene(Scene):
    def construct(self):
        text = Text("Hello World")
        self.add(text)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_scene)
            scene_file = f.name
        
        try:
            # Try to parse (don't actually render)
            import ast
            ast.parse(test_scene)
            print("✓ Basic Manim scene syntax valid")
            return True
            
        finally:
            os.unlink(scene_file)
            
    except Exception as e:
        print(f"✗ Manim test failed: {e}")
        return False

def test_ffmpeg():
    """Test FFmpeg installation"""
    print("\nTesting FFmpeg...")
    
    try:
        import subprocess
        
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg installed: {first_line}")
            return True
        else:
            print("✗ FFmpeg command failed")
            return False
            
    except FileNotFoundError:
        print("✗ FFmpeg not found in PATH")
        return False
    except Exception as e:
        print(f"✗ FFmpeg test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("AI Physics Animator - System Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_schemas,
        test_knowledge_base,
        test_manim_health,
        test_ffmpeg
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*40}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
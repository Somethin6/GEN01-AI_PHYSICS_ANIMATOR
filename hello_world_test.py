#!/usr/bin/env python3
"""
Hello World test for the AI Physics Animator system.
Tests basic pipeline without requiring full LLM setup.
"""

import sys
import tempfile
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))

def test_minimal_scene_generation():
    """Test generating a minimal Manim scene"""
    print("Testing minimal scene generation...")
    
    # Create a simple scene code
    scene_code = '''from manim import *

class HelloScene(Scene):
    def construct(self):
        # Create a simple text object
        title = Text("Hello Physics!", font_size=48)
        title.to_edge(UP)
        
        # Create a simple mathematical expression
        formula = MathTex(r"F = ma")
        formula.scale(2)
        
        # Simple animations
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(FadeIn(formula), run_time=1)
        self.wait(1)
        
        # Transform to another formula
        new_formula = MathTex(r"E = mc^2")
        new_formula.scale(2)
        
        self.play(Transform(formula, new_formula), run_time=1.5)
        self.wait(2)
'''
    
    # Write scene to a temporary file
    scene_dir = Path("manim_project/scenes")
    scene_dir.mkdir(parents=True, exist_ok=True)
    
    scene_file = scene_dir / "hello_scene.py"
    scene_file.write_text(scene_code)
    
    print(f"✓ Generated scene file: {scene_file}")
    return True

def test_schema_creation():
    """Test creating schemas without LLM"""
    print("Testing schema creation...")
    
    try:
        from schemas import ConceptSchema, OutlineSchema, Beat, ValidationResult
        
        # Create a minimal concept
        concept_data = {
            "topic": "Newton's Second Law",
            "audience": "high school",
            "target_duration_sec": 10.0,
            "thesis": "Force equals mass times acceleration",
            "scope": ["F=ma", "force vectors", "acceleration"],
            "prerequisites": ["basic algebra"],
            "risks": ["mixing up mass and weight"],
            "sources": ["Basic Physics Textbook"]
        }
        
        try:
            concept = ConceptSchema.model_validate(concept_data)
        except AttributeError:
            concept = ConceptSchema.parse_obj(concept_data)
        
        print("✓ ConceptSchema created successfully")
        
        # Create a simple outline
        beat_data = {
            "title": "Introduction to F=ma",
            "duration_sec": 5.0,
            "text_script": "Force equals mass times acceleration",
            "math_expressions": ["F = ma"]
        }
        
        try:
            beat = Beat.model_validate(beat_data)
        except AttributeError:
            beat = Beat.parse_obj(beat_data)
            
        outline_data = {
            "beats": [beat],
            "total_duration_sec": 5.0,
            "target_duration_sec": 10.0
        }
        
        try:
            outline = OutlineSchema.model_validate(outline_data)
        except AttributeError:
            outline = OutlineSchema.parse_obj(outline_data)
            
        print("✓ OutlineSchema created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Schema creation failed: {e}")
        return False

def test_render_setup():
    """Test basic render setup without actually rendering"""
    print("Testing render setup...")
    
    try:
        from render import ManimRenderer
        
        # Test renderer initialization
        renderer = ManimRenderer()
        print("✓ ManimRenderer initialized")
        
        # Check directory structure
        if renderer.scenes_dir.exists() and renderer.output_dir.exists():
            print("✓ Directory structure created")
        else:
            print("✗ Directory structure missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Render setup failed: {e}")
        return False

def main():
    """Run hello world tests"""
    print("AI Physics Animator - Hello World Test")
    print("=" * 40)
    
    tests = [
        test_schema_creation,
        test_minimal_scene_generation,
        test_render_setup,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n{'='*40}")
    print(f"Hello World Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 Hello world tests passed! Basic system is functional.")
        return 0
    else:
        print("❌ Some tests failed. Check basic setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
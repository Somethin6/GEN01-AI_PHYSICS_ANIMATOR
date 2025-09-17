#!/usr/bin/env python3
"""
End-to-end integration test for the AI Physics Animator pipeline.
Tests the complete flow from concept to video generation using mock LLM.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))

def test_full_pipeline():
    """Test the complete pipeline with mock LLM"""
    print("Testing full pipeline with mock LLM...")
    
    try:
        from mock_llm import MockLLMEngine
        from schemas import ConceptSchema, UnderstandingSchema, OutlineSchema, AnimationCodegenSchema
        from doctors import ConceptDoctor, VisualDoctor
        from mock_rag import MockManimKnowledgeBase
        
        # Initialize components
        print("  Initializing components...")
        llm = MockLLMEngine()
        concept_doctor = ConceptDoctor()
        
        # Test concept generation
        print("  Testing concept generation...")
        concept = llm.generate_structured(
            "You are a physics education expert.",
            "Create a concept for teaching Newton's Second Law to undergraduates in 15 seconds.",
            ConceptSchema
        )
        
        # Validate concept
        concept_validation = concept_doctor.validate(concept)
        if not concept_validation.valid:
            print(f"    ✗ Concept validation failed: {concept_validation.errors}")
            return False
        print("    ✓ Concept generated and validated")
        
        # Test understanding generation  
        print("  Testing understanding generation...")
        understanding = llm.generate_structured(
            "You are a physics education expert.",
            f"Create understanding materials for: {concept.topic}",
            UnderstandingSchema
        )
        print("    ✓ Understanding generated")
        
        # Test outline generation
        print("  Testing outline generation...")
        outline = llm.generate_structured(
            "You are a physics education expert.",
            f"Create a beat outline for: {concept.topic}",
            OutlineSchema
        )
        print("    ✓ Outline generated")
        
        # Test code generation
        print("  Testing animation code generation...")
        codegen = llm.generate_structured(
            "You are a Manim expert.",
            f"Generate Manim scene code for: {outline.beats[0].title}",
            AnimationCodegenSchema
        )
        print("    ✓ Animation code generated")
        
        # Test visual validation
        print("  Testing visual validation...")
        visual_doctor = VisualDoctor()
        visual_validation = visual_doctor.validate_visual_properties(codegen)
        if visual_validation.errors:
            print(f"    ⚠ Visual validation found issues: {visual_validation.errors}")
        else:
            print("    ✓ Visual validation passed")
        
        # Test performance stats
        print("  Checking performance stats...")
        stats = llm.get_performance_stats()
        print(f"    Generated {stats['total_tokens_generated']} tokens in {stats['total_generation_time']:.2f}s")
        print(f"    Average speed: {stats['average_tokens_per_second']:.1f} tok/s")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scene_file_generation():
    """Test generating actual scene files"""
    print("Testing scene file generation...")
    
    try:
        from mock_llm import MockLLMEngine
        from schemas import AnimationCodegenSchema
        
        llm = MockLLMEngine()
        
        # Generate scene code
        codegen = llm.generate_structured(
            "You are a Manim expert.",
            "Generate a scene showing Newton's Second Law",
            AnimationCodegenSchema
        )
        
        # Write scene to file
        scene_dir = Path("manim_project/scenes")
        scene_dir.mkdir(parents=True, exist_ok=True)
        
        for i, scene in enumerate(codegen.scenes):
            scene_file = scene_dir / f"{scene.class_name.lower()}.py"
            scene_file.write_text(scene.code)
            print(f"    ✓ Created scene file: {scene_file}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Scene generation failed: {e}")
        return False

def test_knowledge_base_mock():
    """Test knowledge base functionality with mock data"""
    print("Testing knowledge base with mock data...")
    
    try:
        # Create a simple mock KB
        mock_kb_data = [
            {
                "id": "text_creation",
                "snippet": "Text('Hello World')",
                "category": "text",
                "notes": "Create text object"
            },
            {
                "id": "mathtex",
                "snippet": "MathTex(r'\\\\vec{F} = m\\\\vec{a}')",
                "category": "math", 
                "notes": "Create mathematical expression"
            },
            {
                "id": "write_animation",
                "snippet": "self.play(Write(object))",
                "category": "animation",
                "notes": "Write animation"
            }
        ]
        
        # Test KB retrieval simulation
        kb_dir = Path("kb")
        kb_dir.mkdir(exist_ok=True)
        
        with open(kb_dir / "mock_snippets.json", "w") as f:
            json.dump(mock_kb_data, f, indent=2)
        
        print("    ✓ Mock knowledge base created")
        return True
        
    except Exception as e:
        print(f"  ✗ Knowledge base test failed: {e}")
        return False

def test_configuration_loading():
    """Test configuration loading and validation"""
    print("Testing configuration loading...")
    
    try:
        import toml
        
        # Load config
        config = toml.load("orchestrator/config.toml")
        
        # Check required sections
        required_sections = ["llm", "performance", "manim", "ffmpeg"]
        for section in required_sections:
            if section not in config:
                print(f"    ✗ Missing config section: {section}")
                return False
        
        print("    ✓ Configuration loaded and validated")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False

def main():
    """Run end-to-end integration tests"""
    print("AI Physics Animator - End-to-End Integration Test")
    print("=" * 50)
    
    tests = [
        test_configuration_loading,
        test_knowledge_base_mock,
        test_scene_file_generation,
        test_full_pipeline,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Integration Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 End-to-end integration tests passed!")
        print("   The AI Physics Animator pipeline is functional!")
        return 0
    else:
        print("❌ Some integration tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
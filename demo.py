#!/usr/bin/env python3
"""
Demo script for the AI Physics Animator system.
Shows complete pipeline from concept to generated Manim scenes.
"""

import sys
import json
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))

def main():
    """Run the AI Physics Animator demo"""
    print("🎬 AI Physics Animator - Demo")
    print("=" * 50)
    print("Generating physics animation with AI pipeline...")
    print()
    
    try:
        from mock_llm import MockLLMEngine
        from schemas import ConceptSchema, OutlineSchema, AnimationCodegenSchema
        from doctors import ConceptDoctor, VisualDoctor
        from mock_rag import MockManimKnowledgeBase
        
        # Initialize system
        print("🔧 Initializing system components...")
        llm = MockLLMEngine()
        concept_doctor = ConceptDoctor()
        visual_doctor = VisualDoctor()
        kb = MockManimKnowledgeBase()
        print("   ✓ All components ready")
        print()
        
        # Step 1: Generate concept
        print("📝 Step 1: Generating physics concept...")
        concept = llm.generate_structured(
            "You are a physics education expert creating engaging animations.",
            "Create a concept for teaching Newton's Second Law with clear visual demonstrations.",
            ConceptSchema
        )
        
        print(f"   Topic: {concept.topic}")
        print(f"   Audience: {concept.audience}")
        print(f"   Duration: {concept.target_duration_sec}s")
        print(f"   Thesis: {concept.thesis}")
        
        # Validate concept
        validation = concept_doctor.validate(concept)
        if validation.valid:
            print("   ✅ Concept validation passed")
        else:
            print(f"   ❌ Concept validation failed: {validation.errors}")
        print()
        
        # Step 2: Generate outline
        print("📋 Step 2: Creating animation outline...")
        outline = llm.generate_structured(
            "You are an animation director creating physics education content.",
            f"Create a detailed beat-by-beat outline for: {concept.topic}",
            OutlineSchema
        )
        
        print(f"   Total duration: {outline.total_duration_sec}s")
        print(f"   Number of beats: {len(outline.beats)}")
        for i, beat in enumerate(outline.beats):
            print(f"     Beat {i+1}: {beat.title} ({beat.duration_sec}s)")
        print()
        
        # Step 3: Generate Manim code
        print("🎨 Step 3: Generating Manim animation code...")
        codegen = llm.generate_structured(
            "You are a Manim expert creating educational physics animations.",
            f"Generate complete Manim scenes for this outline: {[beat.title for beat in outline.beats]}",
            AnimationCodegenSchema
        )
        
        print(f"   Generated {len(codegen.scenes)} scene(s)")
        print()
        
        # Step 4: Visual validation
        print("🔍 Step 4: Running visual quality checks...")
        visual_validation = visual_doctor.validate_visual_properties(codegen)
        
        if visual_validation.valid:
            print("   ✅ All visual quality checks passed")
        else:
            print("   ⚠️  Visual quality issues detected:")
            for error in visual_validation.errors[:3]:  # Show first 3 issues
                print(f"     - {error}")
        print()
        
        # Step 5: Save generated scenes
        print("💾 Step 5: Saving generated scene files...")
        scene_dir = Path("manim_project/scenes")
        scene_dir.mkdir(parents=True, exist_ok=True)
        
        for i, scene in enumerate(codegen.scenes):
            scene_file = scene_dir / f"{scene.class_name.lower()}_demo.py"
            scene_file.write_text(scene.code)
            print(f"   ✓ Saved: {scene_file}")
        print()
        
        # Step 6: Show performance stats
        print("📊 Step 6: Performance statistics...")
        stats = llm.get_performance_stats()
        print(f"   Tokens generated: {stats['total_tokens_generated']}")
        print(f"   Average speed: {stats['average_tokens_per_second']:.1f} tok/s")
        print(f"   Cache entries: {stats['cache_size']}")
        print()
        
        # Demo complete
        print("🎉 Demo completed successfully!")
        print()
        print("Generated files:")
        print(f"   - Scene files in: manim_project/scenes/")
        print(f"   - Knowledge base: kb/mock_snippets.json")
        print()
        print("Next steps:")
        print("   1. Install Manim: pip install manim")
        print("   2. Render scenes: manim -pqh manim_project/scenes/introscene_demo.py IntroScene")
        print("   3. View output in: manim_project/media/")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
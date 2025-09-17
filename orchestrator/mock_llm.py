"""
Mock LLM engine for testing and development without requiring actual model files.
Provides realistic responses for the AI Physics Animator pipeline.
"""

import json
import time
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel

class MockLLMEngine:
    """Mock LLM engine that generates realistic physics animation content"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.prompt_cache = {}
        self.total_tokens_generated = 0
        self.total_generation_time = 0.0
        print("MockLLMEngine initialized (no model file required)")
    
    def generate_structured(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        schema: Type[BaseModel],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        use_cache: bool = True
    ) -> BaseModel:
        """Generate structured mock responses based on schema type"""
        
        # Simulate processing time
        time.sleep(0.1)
        self.total_tokens_generated += 100
        self.total_generation_time += 0.1
        
        schema_name = schema.__name__
        
        # Generate appropriate mock data based on schema type
        if schema_name == "ConceptSchema":
            data = {
                "topic": "Newton's Second Law",
                "audience": "undergraduate",
                "target_duration_sec": 15.0,
                "thesis": "Newton's Second Law establishes the fundamental relationship between force, mass, and acceleration",
                "scope": ["Force definition", "Mass and inertia", "Acceleration vectors", "F=ma derivation"],
                "prerequisites": ["Basic calculus", "Vector mathematics", "Newton's First Law"],
                "risks": ["Confusing mass with weight", "Ignoring vector nature of forces"],
                "sources": ["Halliday, Resnick & Walker Physics", "MIT 8.01 Course Notes"]
            }
            
        elif schema_name == "UnderstandingSchema":
            data = {
                "glossary": {
                    "Force": "A push or pull that can change the motion of an object",
                    "Mass": "The amount of matter in an object, measured in kilograms",
                    "Acceleration": "The rate of change of velocity",
                    "Inertia": "The tendency of an object to resist changes in motion"
                },
                "examples": [
                    {
                        "title": "Ball on Spring",
                        "description": "A ball attached to a spring demonstrates F=ma with restoring force",
                        "kb_citations": ["spring_force", "harmonic_motion"]
                    },
                    {
                        "title": "Car Acceleration", 
                        "description": "Engine force accelerates car mass according to F=ma",
                        "kb_citations": ["force_vectors", "motion_equations"]
                    },
                    {
                        "title": "Falling Object",
                        "description": "Gravitational force creates downward acceleration",
                        "kb_citations": ["gravity", "free_fall"]
                    }
                ],
                "total_examples": 3
            }
            
        elif schema_name == "OutlineSchema":
            data = {
                "beats": [
                    {
                        "title": "Introduction to Force",
                        "duration_sec": 3.0,
                        "text_script": "Forces are pushes and pulls that can change motion",
                        "math_expressions": ["\\vec{F}"]
                    },
                    {
                        "title": "Mass and Inertia",
                        "duration_sec": 4.0,
                        "text_script": "Mass measures how much matter an object contains",
                        "math_expressions": ["m"]
                    },
                    {
                        "title": "Acceleration Definition",
                        "duration_sec": 4.0,
                        "text_script": "Acceleration is the rate of change of velocity",
                        "math_expressions": ["\\vec{a} = \\frac{d\\vec{v}}{dt}"]
                    },
                    {
                        "title": "Newton's Second Law",
                        "duration_sec": 4.0,
                        "text_script": "Force equals mass times acceleration",
                        "math_expressions": ["\\vec{F} = m\\vec{a}"]
                    }
                ],
                "total_duration_sec": 15.0,
                "target_duration_sec": 15.0
            }
            
        elif schema_name == "VideoOutlineSchema":
            data = {
                "beat_visuals": [
                    {
                        "beat_id": 0,
                        "objects": [
                            {
                                "object_type": "Text",
                                "content": "Forces and Motion",
                                "position": "UP",
                                "style": {"font_size": 48}
                            }
                        ],
                        "layout": {
                            "grid_positions": {"title": "UP"},
                            "spacing": 1.0,
                            "alignment": "center"
                        },
                        "animations": [
                            {
                                "animation_type": "Write",
                                "target_objects": ["title"],
                                "duration": 2.0,
                                "easing": "linear"
                            }
                        ],
                        "kb_citations": ["text_creation", "write_animation"]
                    }
                ],
                "allowed_apis": ["Text", "MathTex", "Write", "FadeIn", "Transform"]
            }
            
        elif schema_name == "AnimationCodegenSchema":
            data = {
                "scenes": [
                    {
                        "class_name": "IntroScene", 
                        "code": '''from manim import *

class IntroScene(Scene):
    def construct(self):
        # Create title
        title = Text("Newton's Second Law", font_size=48)
        title.to_edge(UP)
        
        # Create formula
        formula = MathTex(r"\\vec{F} = m\\vec{a}")
        formula.scale(2)
        
        # Animations
        self.play(Write(title), run_time=2)
        self.wait(0.5)
        self.play(FadeIn(formula), run_time=1.5)
        self.wait(1)
''',
                        "imports": ["from manim import *"],
                        "kb_citations": ["text_creation", "mathtex", "write_animation", "fadein"]
                    }
                ],
                "total_scenes": 1
            }
            
        else:
            # Generic response
            data = {"message": f"Mock response for {schema_name}"}
        
        # Convert to schema object
        try:
            return schema.model_validate(data)
        except AttributeError:
            return schema.parse_obj(data)  # Pydantic v1
    
    def generate_text(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> str:
        """Generate plain text mock response"""
        time.sleep(0.1)
        self.total_tokens_generated += 50
        self.total_generation_time += 0.1
        
        return f"Mock text response for prompt: {user_prompt[:50]}..."
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get mock performance statistics"""
        avg_tok_per_sec = 0.0
        if self.total_generation_time > 0:
            avg_tok_per_sec = self.total_tokens_generated / self.total_generation_time
            
        return {
            "model_loaded": True,
            "context_size": 4096,
            "batch_size": 1024,
            "gpu_layers": -1,
            "total_tokens_generated": self.total_tokens_generated,
            "total_generation_time": self.total_generation_time,
            "average_tokens_per_second": avg_tok_per_sec,
            "cache_size": len(self.prompt_cache),
            "mock_mode": True
        }
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self.prompt_cache.clear()
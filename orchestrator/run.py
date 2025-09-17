"""
Main orchestrator - the state machine that coordinates the entire pipeline.
Concept → Understanding → Outline → Derivation → VideoOutline → Codegen → Doctor → Critic → Repair → Render → Compose
"""

import json
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
import toml

from orchestrator.schemas import (
    ConceptSchema, UnderstandingSchema, OutlineSchema,
    DerivationSchema, VideoOutlineSchema, AnimationCodegenSchema,
    ValidationResult, CriticReport
)
from orchestrator.llm_engine import LLMEngine
from orchestrator.rag import ManimKnowledgeBase
from orchestrator.agents import (
    ConceptAgent, UnderstandingAgent, OutlineAgent,
    DerivationAgent, VideoOutlineAgent, AnimationCodegenAgent
)
from orchestrator.doctors import (
    ConceptDoctor, UnderstandingDoctor, OutlineDoctor,
    DerivationDoctor, VideoOutlineDoctor, AnimationDoctor
)
from orchestrator.critic import ManimCritic
from orchestrator.render import ManimRenderer, VideoComposer


class OrchestrationState:
    """Maintains state throughout the pipeline"""
    
    def __init__(self):
        self.concept: Optional[ConceptSchema] = None
        self.understanding: Optional[UnderstandingSchema] = None
        self.outline: Optional[OutlineSchema] = None
        self.derivation: Optional[DerivationSchema] = None
        self.video_outline: Optional[VideoOutlineSchema] = None
        self.codegen: Optional[AnimationCodegenSchema] = None
        self.critic_reports: List[CriticReport] = []
        self.rendered_beats: List[Path] = []
        self.final_video: Optional[Path] = None
        
        # Tracking
        self.current_step: str = "concept"
        self.completed_steps: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.retry_counts: Dict[str, int] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for checkpointing"""
        return {
            "concept": self.concept.dict() if self.concept else None,
            "understanding": self.understanding.dict() if self.understanding else None,
            "outline": self.outline.dict() if self.outline else None,
            "derivation": self.derivation.dict() if self.derivation else None,
            "video_outline": self.video_outline.dict() if self.video_outline else None,
            "codegen": self.codegen.dict() if self.codegen else None,
            "critic_reports": [r.dict() for r in self.critic_reports],
            "rendered_beats": [str(p) for p in self.rendered_beats],
            "final_video": str(self.final_video) if self.final_video else None,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "errors": self.errors,
            "warnings": self.warnings,
            "retry_counts": self.retry_counts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrchestrationState':
        """Deserialize state from checkpoint"""
        state = cls()
        
        if data.get("concept"):
            state.concept = ConceptSchema.model_validate(data["concept"])
        if data.get("understanding"):
            state.understanding = UnderstandingSchema.model_validate(data["understanding"])
        if data.get("outline"):
            state.outline = OutlineSchema.model_validate(data["outline"])
        if data.get("derivation"):
            state.derivation = DerivationSchema.model_validate(data["derivation"])
        if data.get("video_outline"):
            state.video_outline = VideoOutlineSchema.model_validate(data["video_outline"])
        if data.get("codegen"):
            state.codegen = AnimationCodegenSchema.model_validate(data["codegen"])
            
        state.rendered_beats = [Path(p) for p in data.get("rendered_beats", [])]
        state.final_video = Path(data["final_video"]) if data.get("final_video") else None
        state.current_step = data.get("current_step", "concept")
        state.completed_steps = data.get("completed_steps", [])
        state.errors = data.get("errors", [])
        state.warnings = data.get("warnings", [])
        state.retry_counts = data.get("retry_counts", {})
        
        return state


class PhysicsAnimatorOrchestrator:
    """Main orchestrator coordinating the entire pipeline"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config = toml.load(config_path)
        self.config_path = config_path
        
        # Initialize components
        print("Initializing components...")
        self.llm_engine = LLMEngine(config_path)
        self.kb = ManimKnowledgeBase(config_path)
        
        # Initialize agents
        self.concept_agent = ConceptAgent(self.llm_engine)
        self.understanding_agent = UnderstandingAgent(self.llm_engine, self.kb)
        self.outline_agent = OutlineAgent(self.llm_engine)
        self.derivation_agent = DerivationAgent(self.llm_engine)
        self.video_outline_agent = VideoOutlineAgent(self.llm_engine, self.kb)
        self.codegen_agent = AnimationCodegenAgent(self.llm_engine, self.kb)
        
        # Initialize doctors
        self.concept_doctor = ConceptDoctor()
        self.understanding_doctor = UnderstandingDoctor(self.kb)
        self.outline_doctor = OutlineDoctor()
        self.derivation_doctor = DerivationDoctor()
        self.video_outline_doctor = VideoOutlineDoctor(self.kb)
        self.animation_doctor = AnimationDoctor(self.kb)
        
        # Initialize critic and renderer
        self.critic = ManimCritic(config_path)
        self.renderer = ManimRenderer(config_path)
        self.composer = VideoComposer(config_path)
        
        # State management
        self.state = OrchestrationState()
        self.max_retries = self.config["orchestrator"]["max_retries"]
        self.state_file = Path(self.config["orchestrator"]["state_file"])
        
        print("Orchestrator initialized successfully!")
    
    def create_video(self, topic: str, audience: str = "undergraduate", target_duration: float = 15.0) -> Optional[Path]:
        """Main entry point - create a complete video from topic"""
        
        print(f"Creating video for topic: {topic}")
        print(f"Audience: {audience}, Duration: {target_duration}s")
        
        # Load existing state if available
        self._load_checkpoint()
        
        try:
            # Execute pipeline steps
            if not self._run_concept_step(topic, audience, target_duration):
                return None
            
            if not self._run_understanding_step():
                return None
            
            if not self._run_outline_step():
                return None
            
            if not self._run_derivation_step():
                return None
            
            if not self._run_video_outline_step():
                return None
            
            if not self._run_codegen_step():
                return None
            
            if not self._run_critic_step():
                return None
            
            if not self._run_render_step():
                return None
            
            if not self._run_compose_step():
                return None
            
            print(f"Video creation completed: {self.state.final_video}")
            return self.state.final_video
            
        except KeyboardInterrupt:
            print("Process interrupted by user")
            self._save_checkpoint()
            return None
        except Exception as e:
            print(f"Fatal error: {e}")
            traceback.print_exc()
            self._save_checkpoint()
            return None
    
    def _run_concept_step(self, topic: str, audience: str, target_duration: float) -> bool:
        """Step 1: Generate concept breakdown"""
        
        if "concept" in self.state.completed_steps:
            print("Concept step already completed, skipping...")
            return True
        
        print("Step 1: Generating concept...")
        
        for attempt in range(self.max_retries + 1):
            try:
                # Generate concept
                concept = self.concept_agent.generate(topic, audience, target_duration)
                
                # Validate with doctor
                validation = self.concept_doctor.validate(concept)
                
                if validation.valid:
                    self.state.concept = concept
                    self.state.completed_steps.append("concept")
                    self.state.warnings.extend(validation.warnings)
                    self._save_checkpoint()
                    print("Concept generation completed successfully")
                    return True
                else:
                    print(f"Concept validation failed: {validation.errors}")
                    if attempt < self.max_retries:
                        print(f"Retrying... (attempt {attempt + 2}/{self.max_retries + 1})")
                        continue
                    else:
                        self.state.errors.extend(validation.errors)
                        return False
                        
            except Exception as e:
                print(f"Error in concept generation: {e}")
                if attempt < self.max_retries:
                    print(f"Retrying... (attempt {attempt + 2}/{self.max_retries + 1})")
                    continue
                else:
                    self.state.errors.append(f"Concept generation failed: {e}")
                    return False
        
        return False
    
    def _run_understanding_step(self) -> bool:
        """Step 2: Generate understanding materials"""
        
        if "understanding" in self.state.completed_steps:
            print("Understanding step already completed, skipping...")
            return True
        
        print("Step 2: Generating understanding materials...")
        
        for attempt in range(self.max_retries + 1):
            try:
                understanding = self.understanding_agent.generate(self.state.concept)
                validation = self.understanding_doctor.validate(understanding)
                
                if validation.valid:
                    self.state.understanding = understanding
                    self.state.completed_steps.append("understanding")
                    self.state.warnings.extend(validation.warnings)
                    self._save_checkpoint()
                    print("Understanding generation completed successfully")
                    return True
                else:
                    print(f"Understanding validation failed: {validation.errors}")
                    if attempt < self.max_retries:
                        continue
                    else:
                        self.state.errors.extend(validation.errors)
                        return False
                        
            except Exception as e:
                print(f"Error in understanding generation: {e}")
                if attempt < self.max_retries:
                    continue
                else:
                    self.state.errors.append(f"Understanding generation failed: {e}")
                    return False
        
        return False
    
    def _run_outline_step(self) -> bool:
        """Step 3: Generate outline"""
        
        if "outline" in self.state.completed_steps:
            print("Outline step already completed, skipping...")
            return True
        
        print("Step 3: Generating outline...")
        
        for attempt in range(self.max_retries + 1):
            try:
                outline = self.outline_agent.generate(self.state.concept, self.state.understanding)
                validation = self.outline_doctor.validate(outline)
                
                if validation.valid:
                    self.state.outline = outline
                    self.state.completed_steps.append("outline")
                    self.state.warnings.extend(validation.warnings)
                    self._save_checkpoint()
                    print("Outline generation completed successfully")
                    return True
                else:
                    print(f"Outline validation failed: {validation.errors}")
                    if attempt < self.max_retries:
                        continue
                    else:
                        self.state.errors.extend(validation.errors)
                        return False
                        
            except Exception as e:
                print(f"Error in outline generation: {e}")
                if attempt < self.max_retries:
                    continue
                else:
                    self.state.errors.append(f"Outline generation failed: {e}")
                    return False
        
        return False
    
    def _run_derivation_step(self) -> bool:
        """Step 4: Generate mathematical derivation"""
        
        if "derivation" in self.state.completed_steps:
            print("Derivation step already completed, skipping...")
            return True
        
        print("Step 4: Generating mathematical derivation...")
        
        for attempt in range(self.max_retries + 1):
            try:
                derivation = self.derivation_agent.generate(self.state.concept, self.state.outline)
                validation = self.derivation_doctor.validate(derivation)
                
                if validation.valid:
                    self.state.derivation = derivation
                    self.state.completed_steps.append("derivation")
                    self.state.warnings.extend(validation.warnings)
                    self._save_checkpoint()
                    print("Derivation generation completed successfully")
                    return True
                else:
                    print(f"Derivation validation failed: {validation.errors}")
                    if attempt < self.max_retries:
                        continue
                    else:
                        self.state.errors.extend(validation.errors)
                        return False
                        
            except Exception as e:
                print(f"Error in derivation generation: {e}")
                if attempt < self.max_retries:
                    continue
                else:
                    self.state.errors.append(f"Derivation generation failed: {e}")
                    return False
        
        return False
    
    def _run_video_outline_step(self) -> bool:
        """Step 5: Generate video outline"""
        
        if "video_outline" in self.state.completed_steps:
            print("Video outline step already completed, skipping...")
            return True
        
        print("Step 5: Generating video outline...")
        
        for attempt in range(self.max_retries + 1):
            try:
                video_outline = self.video_outline_agent.generate(self.state.outline, self.state.derivation)
                validation = self.video_outline_doctor.validate(video_outline)
                
                if validation.valid:
                    self.state.video_outline = video_outline
                    self.state.completed_steps.append("video_outline")
                    self.state.warnings.extend(validation.warnings)
                    self._save_checkpoint()
                    print("Video outline generation completed successfully")
                    return True
                else:
                    print(f"Video outline validation failed: {validation.errors}")
                    if attempt < self.max_retries:
                        continue
                    else:
                        self.state.errors.extend(validation.errors)
                        return False
                        
            except Exception as e:
                print(f"Error in video outline generation: {e}")
                if attempt < self.max_retries:
                    continue
                else:
                    self.state.errors.append(f"Video outline generation failed: {e}")
                    return False
        
        return False
    
    def _run_codegen_step(self) -> bool:
        """Step 6: Generate Manim code"""
        
        if "codegen" in self.state.completed_steps:
            print("Codegen step already completed, skipping...")
            return True
        
        print("Step 6: Generating Manim code...")
        
        for attempt in range(self.max_retries + 1):
            try:
                codegen = self.codegen_agent.generate(self.state.video_outline, self.state.outline)
                validation = self.animation_doctor.validate(codegen)
                
                if validation.valid:
                    self.state.codegen = codegen
                    self.state.completed_steps.append("codegen")
                    self.state.warnings.extend(validation.warnings)
                    self._save_checkpoint()
                    print("Code generation completed successfully")
                    return True
                else:
                    print(f"Code validation failed: {validation.errors}")
                    if attempt < self.max_retries:
                        continue
                    else:
                        self.state.errors.extend(validation.errors)
                        return False
                        
            except Exception as e:
                print(f"Error in code generation: {e}")
                if attempt < self.max_retries:
                    continue
                else:
                    self.state.errors.append(f"Code generation failed: {e}")
                    return False
        
        return False
    
    def _run_critic_step(self) -> bool:
        """Step 7: Analyze code with visual critic"""
        
        if "critic" in self.state.completed_steps:
            print("Critic step already completed, skipping...")
            return True
        
        print("Step 7: Running visual critic...")
        
        try:
            reports = []
            for scene in self.state.codegen.scenes:
                report = self.critic.analyze_scene(scene.code, scene.class_name)
                reports.append(report)
            
            self.state.critic_reports = reports
            
            # Apply patches if any
            total_patches = sum(len(r.patches) for r in reports)
            if total_patches > 0:
                print(f"Critic found {total_patches} issues, applying patches...")
                # TODO: Implement patch application
                # For now, just warn
                self.state.warnings.append(f"Critic found {total_patches} visual issues")
            
            self.state.completed_steps.append("critic")
            self._save_checkpoint()
            print("Visual critic analysis completed")
            return True
            
        except Exception as e:
            print(f"Error in critic analysis: {e}")
            self.state.errors.append(f"Critic analysis failed: {e}")
            return False
    
    def _run_render_step(self) -> bool:
        """Step 8: Render individual beats"""
        
        if "render" in self.state.completed_steps:
            print("Render step already completed, skipping...")
            return True
        
        print("Step 8: Rendering beats...")
        
        try:
            # Render fast quality first for validation
            fast_files = self.renderer.render_all_beats(self.state.codegen, quality="low")
            
            if len(fast_files) != len(self.state.codegen.scenes):
                self.state.errors.append(f"Only {len(fast_files)}/{len(self.state.codegen.scenes)} beats rendered successfully")
                return False
            
            # If fast render succeeded, do high quality
            print("Fast render successful, starting high quality render...")
            final_files = self.renderer.render_all_beats(self.state.codegen, quality="high")
            
            if len(final_files) != len(self.state.codegen.scenes):
                print("High quality render failed, using low quality files")
                final_files = fast_files
            
            self.state.rendered_beats = final_files
            self.state.completed_steps.append("render")
            self._save_checkpoint()
            print("Rendering completed successfully")
            return True
            
        except Exception as e:
            print(f"Error in rendering: {e}")
            self.state.errors.append(f"Rendering failed: {e}")
            return False
    
    def _run_compose_step(self) -> bool:
        """Step 9: Compose final video"""
        
        if "compose" in self.state.completed_steps:
            print("Compose step already completed, skipping...")
            return True
        
        print("Step 9: Composing final video...")
        
        try:
            # Validate stream compatibility
            if not self.composer.validate_streams(self.state.rendered_beats):
                self.state.errors.append("Beat files have incompatible streams for concatenation")
                return False
            
            # Compose final video
            final_video = self.composer.compose_video(self.state.rendered_beats, "physics_animation")
            
            if final_video and final_video.exists():
                self.state.final_video = final_video
                self.state.completed_steps.append("compose")
                self._save_checkpoint()
                print("Video composition completed successfully")
                return True
            else:
                self.state.errors.append("Video composition failed")
                return False
                
        except Exception as e:
            print(f"Error in composition: {e}")
            self.state.errors.append(f"Composition failed: {e}")
            return False
    
    def _save_checkpoint(self):
        """Save current state to checkpoint file"""
        try:
            checkpoint_data = self.state.to_dict()
            checkpoint_data["timestamp"] = time.time()
            
            with open(self.state_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to save checkpoint: {e}")
    
    def _load_checkpoint(self):
        """Load state from checkpoint file if it exists"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    checkpoint_data = json.load(f)
                
                self.state = OrchestrationState.from_dict(checkpoint_data)
                print(f"Loaded checkpoint from {self.state_file}")
                print(f"Completed steps: {self.state.completed_steps}")
                
            except Exception as e:
                print(f"Warning: Failed to load checkpoint: {e}")
                self.state = OrchestrationState()
    
    def reset_state(self):
        """Reset orchestrator state and delete checkpoint"""
        self.state = OrchestrationState()
        if self.state_file.exists():
            self.state_file.unlink()
        print("Orchestrator state reset")


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Physics Animator")
    parser.add_argument("--topic", required=True, help="Physics topic to animate")
    parser.add_argument("--audience", default="undergraduate", help="Target audience")
    parser.add_argument("--duration", type=float, default=15.0, help="Target duration in seconds")
    parser.add_argument("--config", default="orchestrator/config.toml", help="Config file path")
    parser.add_argument("--reset", action="store_true", help="Reset state and start fresh")
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = PhysicsAnimatorOrchestrator(args.config)
    
    if args.reset:
        orchestrator.reset_state()
    
    # Create video
    result = orchestrator.create_video(args.topic, args.audience, args.duration)
    
    if result:
        print(f"\n🎉 Success! Video created: {result}")
    else:
        print(f"\n❌ Failed to create video. Errors: {orchestrator.state.errors}")


if __name__ == "__main__":
    main()
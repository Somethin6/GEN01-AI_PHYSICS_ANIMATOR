"""
AI Agents for each layer of the physics animation pipeline.
Uses structured JSON generation with schema validation.
"""

from typing import List, Dict, Any
from orchestrator.schemas import (
    ConceptSchema, UnderstandingSchema, OutlineSchema, 
    DerivationSchema, VideoOutlineSchema, AnimationCodegenSchema
)
from orchestrator.llm_engine import LLMEngine
from orchestrator.rag import ManimKnowledgeBase


class ConceptAgent:
    """Converts topic into structured concept with scope and prerequisites"""
    
    def __init__(self, llm_engine: LLMEngine):
        self.llm = llm_engine
    
    def generate(self, topic: str, audience: str = "undergraduate", target_duration: float = 15.0) -> ConceptSchema:
        system_prompt = """You are a physics education expert. Convert a topic into a structured concept breakdown.
        
Focus on:
- Clear thesis statement
- Realistic scope for the duration
- Essential prerequisites 
- Common misconceptions to address
- Authoritative sources"""
        
        user_prompt = f"""Topic: {topic}
Audience: {audience}
Target Duration: {target_duration} seconds

Create a concept breakdown that addresses the core physics principles while being achievable in the given timeframe."""
        
        return self.llm.generate_structured(system_prompt, user_prompt, ConceptSchema)


class UnderstandingAgent:
    """Creates glossary and atomic examples with KB citations"""
    
    def __init__(self, llm_engine: LLMEngine, kb: ManimKnowledgeBase):
        self.llm = llm_engine
        self.kb = kb
    
    def generate(self, concept: ConceptSchema) -> UnderstandingSchema:
        # Retrieve relevant KB snippets
        relevant_snippets = self.kb.retrieve(f"{concept.topic} {' '.join(concept.scope)}")
        
        system_prompt = """You are a physics educator creating foundational understanding materials.

Create 3-5 atomic examples that demonstrate the core concepts. Each example must:
- Be self-contained and buildable in Manim
- Reference specific knowledge base snippets by ID
- Show concrete physics principles

Available Knowledge Base Snippets:"""
        
        for snippet in relevant_snippets:
            system_prompt += f"\n- ID: {snippet['id']}: {snippet['snippet']} ({snippet['notes']})"
        
        user_prompt = f"""Concept: {concept.thesis}
Scope: {concept.scope}
Prerequisites: {concept.prerequisites}

Create glossary definitions and 3-5 atomic examples that build understanding.
Each example must cite specific KB snippet IDs that will be used to implement it."""
        
        return self.llm.generate_structured(system_prompt, user_prompt, UnderstandingSchema)


class OutlineAgent:
    """Creates beat-by-beat outline with precise timing"""
    
    def __init__(self, llm_engine: LLMEngine):
        self.llm = llm_engine
    
    def generate(self, concept: ConceptSchema, understanding: UnderstandingSchema) -> OutlineSchema:
        system_prompt = """You are a video production expert creating precise beat sheets.

Each beat must:
- Have clear learning objective
- Fit within duration constraints
- Include specific script text
- List mathematical expressions needed
- Build logically on previous beats

Total duration must be within ±5% of target."""
        
        user_prompt = f"""Target Duration: {concept.target_duration_sec} seconds
Concept: {concept.thesis}
Key Examples: {[ex.title for ex in understanding.examples]}

Create a beat sheet that covers the concept systematically within the time constraint.
Each beat should be 2-4 seconds for clarity."""
        
        return self.llm.generate_structured(system_prompt, user_prompt, OutlineSchema)


class DerivationAgent:
    """Creates mathematical derivations with step-by-step reasoning"""
    
    def __init__(self, llm_engine: LLMEngine):
        self.llm = llm_engine
    
    def generate(self, concept: ConceptSchema, outline: OutlineSchema) -> DerivationSchema:
        system_prompt = """You are a theoretical physicist creating rigorous mathematical derivations.

Each step must:
- Show clear mathematical progression  
- Explain physical reasoning
- State assumptions explicitly
- Maintain algebraic consistency
- Connect to the visual narrative"""
        
        user_prompt = f"""Topic: {concept.topic}
Mathematical expressions needed: {[beat.math_expressions for beat in outline.beats]}

Create a complete derivation that supports the visual narrative.
Show all algebraic steps and physical reasoning."""
        
        return self.llm.generate_structured(system_prompt, user_prompt, DerivationSchema)


class VideoOutlineAgent:
    """Maps beats to specific Manim objects and animations"""
    
    def __init__(self, llm_engine: LLMEngine, kb: ManimKnowledgeBase):
        self.llm = llm_engine
        self.kb = kb
    
    def generate(self, outline: OutlineSchema, derivation: DerivationSchema) -> VideoOutlineSchema:
        # Get all available Manim APIs
        all_snippets = self.kb.get_all_snippets()
        allowed_apis = [s['snippet'].split('(')[0] for s in all_snippets]
        
        system_prompt = """You are a Manim expert creating precise visual specifications.

For each beat, specify:
- Exact Manim objects (Text, MathTex, Axes, etc.)
- Layout using next_to, arrange, to_edge
- Animations (Write, FadeIn, Transform, etc.)
- Only use APIs from the knowledge base

Available Manim APIs:"""
        
        for snippet in all_snippets:
            system_prompt += f"\n- {snippet['id']}: {snippet['snippet']} - {snippet['notes']}"
        
        user_prompt = f"""Beats to visualize:
{[f"Beat {i+1}: {beat.title} ({beat.duration_sec}s)" for i, beat in enumerate(outline.beats)]}

Derivation steps:
{[f"Step {step.step_number}: {step.equation}" for step in derivation.steps]}

Create visual specifications for each beat. Only use APIs from the knowledge base."""
        
        return self.llm.generate_structured(system_prompt, user_prompt, VideoOutlineSchema)


class AnimationCodegenAgent:
    """Generates actual Manim scene code"""
    
    def __init__(self, llm_engine: LLMEngine, kb: ManimKnowledgeBase):
        self.llm = llm_engine  
        self.kb = kb
    
    def generate(self, video_outline: VideoOutlineSchema, outline: OutlineSchema) -> AnimationCodegenSchema:
        # Retrieve relevant code snippets
        all_citations = []
        for beat_visual in video_outline.beat_visuals:
            all_citations.extend(beat_visual.kb_citations)
        
        relevant_snippets = []
        for citation_id in set(all_citations):
            snippet = self.kb.get_snippet_by_id(citation_id)
            if snippet:
                relevant_snippets.append(snippet)
        
        system_prompt = """You are a Manim expert generating production-ready scene code.

Requirements:
- One Scene class per beat
- Use only validated APIs from knowledge base
- Include proper imports
- Follow Manim CE 0.19+ conventions
- Clean, readable code structure
- Comment with KB citation IDs

Referenced Knowledge Base:"""
        
        for snippet in relevant_snippets:
            system_prompt += f"\n# KB: {snippet['id']}\n{snippet['snippet']} # {snippet['notes']}\n"
        
        beats_info = []
        for i, (beat, visual) in enumerate(zip(outline.beats, video_outline.beat_visuals)):
            beats_info.append(f"Beat {i+1}: {beat.title} ({beat.duration_sec}s)\n  Script: {beat.text_script}\n  Objects: {[obj.object_type for obj in visual.objects]}\n  Animations: {[anim.animation_type for anim in visual.animations]}")
        
        user_prompt = f"""Generate Manim scene classes for these beats:

{chr(10).join(beats_info)}

Each scene should be self-contained and implement the specified visual design.
Use KB citations in comments: # KB: [id1, id2]"""
        
        return self.llm.generate_structured(system_prompt, user_prompt, AnimationCodegenSchema)
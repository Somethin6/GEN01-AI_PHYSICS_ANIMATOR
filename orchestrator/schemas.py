"""
Pydantic schemas defining the contracts between pipeline layers.
Each schema has a corresponding Doctor for validation.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
try:
    from pydantic import validator  # Pydantic v1 style
except ImportError:
    from pydantic import field_validator as validator  # Pydantic v2 style
from enum import Enum


class ConceptSchema(BaseModel):
    """Input: topic, audience, target_duration_sec → Output: thesis, scope, prerequisites, risks, sources"""
    topic: str = Field(..., description="The physics topic to animate")
    audience: str = Field(..., description="Target audience level")
    target_duration_sec: float = Field(..., gt=0, description="Target video duration in seconds")
    
    thesis: str = Field(..., description="Core thesis statement")
    scope: List[str] = Field(..., description="List of concepts to cover")
    prerequisites: List[str] = Field(..., description="Required background knowledge")
    risks: List[str] = Field(..., description="Common misconceptions to address")
    sources: List[str] = Field(..., description="Reference sources")


class UnderstandingSchema(BaseModel):
    """Glossary + 3-5 atomic examples, each grounded in KB link/citation"""
    
    class Example(BaseModel):
        title: str
        description: str
        kb_citations: List[str] = Field(..., description="Knowledge base snippet IDs")
        
    glossary: Dict[str, str] = Field(..., description="Key terms and definitions")
    examples: List[Example] = Field(..., min_items=3, max_items=5)
    total_examples: int = Field(..., ge=3, le=5)


class Beat(BaseModel):
    """Individual beat in the outline"""
    title: str
    duration_sec: float = Field(..., gt=0)
    text_script: str
    math_expressions: List[str] = Field(default_factory=list)
    
    @validator('duration_sec')
    def duration_positive(cls, v):
        if v <= 0:
            raise ValueError('Duration must be positive')
        return v


class OutlineSchema(BaseModel):
    """Beat sheet with duration validation"""
    beats: List[Beat] = Field(..., min_items=1)
    total_duration_sec: float = Field(..., gt=0)
    target_duration_sec: float = Field(..., gt=0)
    
    @validator('total_duration_sec', always=True)
    def validate_total_duration(cls, v, values):
        if 'beats' in values:
            calculated = sum(beat.duration_sec for beat in values['beats'])
            if abs(calculated - v) > 0.1:  # Allow small floating point errors
                raise ValueError(f'Total duration {v} does not match sum of beats {calculated}')
        return v
        
    @validator('total_duration_sec')
    def duration_within_tolerance(cls, v, values):
        if 'target_duration_sec' in values:
            target = values['target_duration_sec']
            tolerance = 0.05  # ±5%
            if abs(v - target) > target * tolerance:
                raise ValueError(f'Duration {v}s is outside ±5% of target {target}s')
        return v


class DerivationStep(BaseModel):
    """Single step in mathematical derivation"""
    step_number: int
    equation: str
    explanation: str
    justification: str
    assumptions: List[str] = Field(default_factory=list)


class DerivationSchema(BaseModel):
    """Math/logic steps with local consistency checks"""
    steps: List[DerivationStep] = Field(..., min_items=1)
    initial_conditions: List[str]
    final_result: str
    validation_notes: List[str] = Field(default_factory=list)


class ManimObject(BaseModel):
    """Manim object specification"""
    object_type: str = Field(..., description="Text, MathTex, SVGMobject, etc.")
    content: str
    position: Optional[str] = Field(None, description="Position specification")
    style: Dict[str, Any] = Field(default_factory=dict)


class Layout(BaseModel):
    """Layout specification for objects"""
    grid_positions: Dict[str, str] = Field(default_factory=dict)
    spacing: float = Field(default=1.0)
    alignment: str = Field(default="center")


class Animation(BaseModel):
    """Animation specification"""
    animation_type: str = Field(..., description="Write, FadeIn, Transform, etc.")
    target_objects: List[str]
    duration: float = Field(..., gt=0)
    easing: str = Field(default="linear")


class VideoOutlineSchema(BaseModel):
    """Per beat: objects, layout, animations - only allowed APIs"""
    
    class BeatVisual(BaseModel):
        beat_id: int
        objects: List[ManimObject]
        layout: Layout
        animations: List[Animation]
        kb_citations: List[str] = Field(..., description="KB snippet IDs used")
        
    beat_visuals: List[BeatVisual] = Field(..., min_items=1)
    allowed_apis: List[str] = Field(default_factory=list)


class SceneCode(BaseModel):
    """Generated Manim scene code"""
    class_name: str
    code: str
    imports: List[str]
    kb_citations: List[str] = Field(..., description="KB snippet IDs referenced")


class AnimationCodegenSchema(BaseModel):
    """One scene per beat with validation"""
    scenes: List[SceneCode] = Field(..., min_items=1)
    total_scenes: int = Field(..., ge=1)
    
    @validator('total_scenes', always=True)
    def validate_scene_count(cls, v, values):
        if 'scenes' in values and len(values['scenes']) != v:
            raise ValueError(f'Scene count {v} does not match actual scenes {len(values["scenes"])}')
        return v


class ValidationResult(BaseModel):
    """Standard validation result format"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CriticPatch(BaseModel):
    """Visual critic patch suggestion"""
    issue_type: str = Field(..., description="overlap, off_screen, occlusion, low_contrast")
    description: str
    code_edit: str = Field(..., description="Exact code to apply")
    line_number: Optional[int] = None


class CriticReport(BaseModel):
    """Visual critic analysis report"""
    scene_name: str
    patches: List[CriticPatch] = Field(default_factory=list)
    contrast_ratios: Dict[str, float] = Field(default_factory=dict)
    bounding_boxes: Dict[str, List[float]] = Field(default_factory=dict)
    z_order_issues: List[str] = Field(default_factory=list)
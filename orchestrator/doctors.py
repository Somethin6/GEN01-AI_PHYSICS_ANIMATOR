"""
Doctor validation system for each pipeline layer.
Ensures data quality and consistency between stages.
"""

import ast
import re
import importlib.util
from typing import List, Dict, Any, Set
from pathlib import Path

from orchestrator.schemas import (
    ConceptSchema, UnderstandingSchema, OutlineSchema,
    DerivationSchema, VideoOutlineSchema, AnimationCodegenSchema,
    ValidationResult
)
from orchestrator.rag import ManimKnowledgeBase


class ConceptDoctor:
    """Validates concept schema output"""
    
    def validate(self, concept: ConceptSchema) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []
        
        # Check thesis clarity
        if len(concept.thesis) < 20:
            errors.append("Thesis statement too short - needs more detail")
        
        # Check scope reasonableness for duration
        if len(concept.scope) > concept.target_duration_sec / 2:
            warnings.append(f"Scope might be too ambitious for {concept.target_duration_sec}s video")
        
        # Check for prerequisites
        if not concept.prerequisites:
            warnings.append("No prerequisites specified - consider if background knowledge is needed")
        
        # Check for risk awareness
        if not concept.risks:
            warnings.append("No misconceptions identified - consider common student errors")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


class UnderstandingDoctor:
    """Validates understanding schema and KB citations"""
    
    def __init__(self, kb: ManimKnowledgeBase):
        self.kb = kb
    
    def validate(self, understanding: UnderstandingSchema) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []
        
        # Check example count
        if not (3 <= len(understanding.examples) <= 5):
            errors.append(f"Must have 3-5 examples, got {len(understanding.examples)}")
        
        # Validate KB citations
        all_kb_ids = {s['id'] for s in self.kb.get_all_snippets()}
        
        for i, example in enumerate(understanding.examples):
            if not example.kb_citations:
                errors.append(f"Example {i+1} has no KB citations")
            else:
                invalid_citations = set(example.kb_citations) - all_kb_ids
                if invalid_citations:
                    errors.append(f"Example {i+1} has invalid KB citations: {invalid_citations}")
        
        # Check glossary completeness
        if len(understanding.glossary) < 3:
            warnings.append("Glossary seems sparse - consider adding more key terms")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


class OutlineDoctor:
    """Validates outline timing and structure"""
    
    def validate(self, outline: OutlineSchema) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []
        
        # Check duration consistency (already enforced by schema validators)
        calculated_duration = sum(beat.duration_sec for beat in outline.beats)
        if abs(calculated_duration - outline.total_duration_sec) > 0.1:
            errors.append(f"Duration mismatch: calculated {calculated_duration}s vs claimed {outline.total_duration_sec}s")
        
        # Check target tolerance
        target = outline.target_duration_sec
        tolerance = 0.05
        if abs(outline.total_duration_sec - target) > target * tolerance:
            errors.append(f"Total duration {outline.total_duration_sec}s outside ±5% of target {target}s")
        
        # Check beat length reasonableness
        for i, beat in enumerate(outline.beats):
            if beat.duration_sec < 1.0:
                warnings.append(f"Beat {i+1} very short ({beat.duration_sec}s) - might be too fast")
            elif beat.duration_sec > 8.0:
                warnings.append(f"Beat {i+1} very long ({beat.duration_sec}s) - consider splitting")
        
        # Check script content
        for i, beat in enumerate(outline.beats):
            if len(beat.text_script.split()) < 3:
                warnings.append(f"Beat {i+1} script seems too short")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


class DerivationDoctor:
    """Validates mathematical derivation consistency"""
    
    def validate(self, derivation: DerivationSchema) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []
        
        # Check step numbering
        expected_steps = list(range(1, len(derivation.steps) + 1))
        actual_steps = [step.step_number for step in derivation.steps]
        if actual_steps != expected_steps:
            errors.append(f"Step numbering incorrect: expected {expected_steps}, got {actual_steps}")
        
        # Check for equation consistency (basic regex validation)
        for i, step in enumerate(derivation.steps):
            if not step.equation.strip():
                errors.append(f"Step {i+1} has empty equation")
            if not step.explanation.strip():
                errors.append(f"Step {i+1} has empty explanation")
        
        # Check for assumptions documentation
        total_assumptions = sum(len(step.assumptions) for step in derivation.steps)
        if total_assumptions == 0:
            warnings.append("No assumptions documented - consider if any simplifications were made")
        
        # Basic equation format check
        for i, step in enumerate(derivation.steps):
            if '=' not in step.equation:
                warnings.append(f"Step {i+1} equation might not be properly formatted (no '=' found)")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


class VideoOutlineDoctor:
    """Validates video outline against allowed Manim APIs"""
    
    def __init__(self, kb: ManimKnowledgeBase):
        self.kb = kb
    
    def validate(self, video_outline: VideoOutlineSchema) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []
        
        # Get allowed APIs from KB
        all_snippets = self.kb.get_all_snippets()
        allowed_object_types = set()
        allowed_animations = set()
        
        for snippet in all_snippets:
            if snippet['category'] in ['text', 'math', 'shapes', 'plotting']:
                api_name = snippet['snippet'].split('(')[0]
                allowed_object_types.add(api_name)
            elif snippet['category'] == 'animation':
                api_name = snippet['snippet'].split('(')[0].replace('self.play(', '').replace('(', '')
                allowed_animations.add(api_name)
        
        # Validate each beat
        for i, beat_visual in enumerate(video_outline.beat_visuals):
            # Check object types
            for obj in beat_visual.objects:
                if obj.object_type not in allowed_object_types:
                    errors.append(f"Beat {i+1}: Unknown object type '{obj.object_type}'")
            
            # Check animation types  
            for anim in beat_visual.animations:
                if anim.animation_type not in allowed_animations:
                    errors.append(f"Beat {i+1}: Unknown animation type '{anim.animation_type}'")
            
            # Check KB citations
            all_kb_ids = {s['id'] for s in all_snippets}
            invalid_citations = set(beat_visual.kb_citations) - all_kb_ids
            if invalid_citations:
                errors.append(f"Beat {i+1}: Invalid KB citations {invalid_citations}")
            
            # Check animation durations
            total_anim_duration = sum(anim.duration for anim in beat_visual.animations)
            if total_anim_duration > 10.0:  # Reasonable upper bound
                warnings.append(f"Beat {i+1}: Very long animation sequence ({total_anim_duration}s)")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


class AnimationDoctor:
    """Validates generated Manim code"""
    
    def __init__(self, kb: ManimKnowledgeBase):
        self.kb = kb
    
    def validate(self, codegen: AnimationCodegenSchema) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []
        
        # Validate each scene
        for i, scene in enumerate(codegen.scenes):
            # Check imports
            if not self._validate_imports(scene.imports):
                errors.append(f"Scene {i+1}: Invalid or missing imports")
            
            # Check code syntax
            syntax_errors = self._check_syntax(scene.code)
            if syntax_errors:
                errors.extend([f"Scene {i+1}: {err}" for err in syntax_errors])
            
            # Check for allowed APIs only
            api_violations = self._check_api_usage(scene.code, scene.kb_citations)
            if api_violations:
                errors.extend([f"Scene {i+1}: {err}" for err in api_violations])
            
            # Check class structure
            if not self._validate_class_structure(scene.code, scene.class_name):
                errors.append(f"Scene {i+1}: Invalid class structure")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _validate_imports(self, imports: List[str]) -> bool:
        """Check if imports are valid"""
        required_imports = {'manim'}
        allowed_imports = {'manim', 'numpy', 'math', 'typing'}
        
        import_modules = set()
        for imp in imports:
            if imp.startswith('from '):
                module = imp.split()[1].split('.')[0]
                import_modules.add(module)
            elif imp.startswith('import '):
                module = imp.split()[1].split('.')[0]
                import_modules.add(module)
        
        # Check required imports present
        if not required_imports.issubset(import_modules):
            return False
        
        # Check only allowed imports used
        if not import_modules.issubset(allowed_imports):
            return False
        
        return True
    
    def _check_syntax(self, code: str) -> List[str]:
        """Check Python syntax"""
        try:
            ast.parse(code)
            return []
        except SyntaxError as e:
            return [f"Syntax error: {e.msg} at line {e.lineno}"]
    
    def _check_api_usage(self, code: str, citations: List[str]) -> List[str]:
        """Check that only cited APIs are used"""
        errors = []
        
        # Get allowed APIs from citations
        allowed_apis = set()
        for citation_id in citations:
            snippet = self.kb.get_snippet_by_id(citation_id)
            if snippet:
                api_name = snippet['snippet'].split('(')[0]
                # Handle different API patterns
                if '.' in api_name:
                    allowed_apis.add(api_name.split('.')[-1])
                else:
                    allowed_apis.add(api_name)
        
        # Basic API usage detection (can be enhanced)
        manim_calls = re.findall(r'\b([A-Z][a-zA-Z]*)\(', code)
        for api_call in set(manim_calls):
            if api_call not in allowed_apis and api_call != 'Scene':  # Scene is always allowed
                errors.append(f"Uncited API usage: {api_call}")
        
        return errors
    
    def _validate_class_structure(self, code: str, expected_class_name: str) -> bool:
        """Check that code has proper Scene class structure"""
        try:
            tree = ast.parse(code)
            
            # Find class definitions
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            
            if len(classes) != 1:
                return False
            
            scene_class = classes[0]
            if scene_class.name != expected_class_name:
                return False
            
            # Check inheritance (should inherit from Scene)
            if not scene_class.bases:
                return False
            
            # Look for construct method
            methods = [node for node in scene_class.body if isinstance(node, ast.FunctionDef)]
            construct_methods = [m for m in methods if m.name == 'construct']
            
            if len(construct_methods) != 1:
                return False
            
            return True
        except:
            return False
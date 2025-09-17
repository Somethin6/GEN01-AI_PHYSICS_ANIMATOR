"""
Visual Critic using Manim's own geometry APIs.
Analyzes animations by sampling at key points and reading bounding boxes.
No computer vision or frame analysis needed.
"""

import ast
import tempfile
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import importlib.util

from orchestrator.schemas import CriticReport, CriticPatch
import toml

# Color contrast calculation (WCAG 2.1 standard)
def luminance(hex_color: str) -> float:
    """Calculate relative luminance for WCAG contrast"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    if len(hex_color) == 3:
        r, g, b = [int(hex_color[i], 16) * 17 for i in range(3)]
    elif len(hex_color) == 6:
        r, g, b = [int(hex_color[i:i+2], 16) for i in range(0, 6, 2)]
    else:
        return 0.5  # Default for invalid colors
    
    # Convert to relative luminance
    def gamma_correct(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r_lin = gamma_correct(r)
    g_lin = gamma_correct(g)
    b_lin = gamma_correct(b)
    
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two colors"""
    l1 = luminance(color1)
    l2 = luminance(color2)
    
    # Ensure l1 is the lighter color
    if l2 > l1:
        l1, l2 = l2, l1
    
    return (l1 + 0.05) / (l2 + 0.05)


class ManimCritic:
    """Analyzes Manim scenes using geometry APIs"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config = toml.load(config_path)["critic"]
        self.background_color = "#000000"  # Default Manim background
        
    def analyze_scene(self, scene_code: str, scene_class_name: str) -> CriticReport:
        """Analyze a Manim scene for visual issues"""
        
        # Create temporary scene file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(scene_code)
            scene_file = f.name
        
        try:
            # Import and analyze the scene
            report = self._analyze_scene_geometry(scene_file, scene_class_name)
        except Exception as e:
            # Return error report if analysis fails
            report = CriticReport(
                scene_name=scene_class_name,
                patches=[CriticPatch(
                    issue_type="analysis_error",
                    description=f"Failed to analyze scene: {str(e)}",
                    code_edit="# Analysis failed - check scene code syntax"
                )]
            )
        finally:
            # Clean up temp file
            Path(scene_file).unlink(missing_ok=True)
        
        return report
    
    def _analyze_scene_geometry(self, scene_file: str, scene_class_name: str) -> CriticReport:
        """Analyze scene using Manim's geometry APIs"""
        
        # Import the scene dynamically
        spec = importlib.util.spec_from_file_location("temp_scene", scene_file)
        scene_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scene_module)
        
        scene_class = getattr(scene_module, scene_class_name)
        
        patches = []
        bounding_boxes = {}
        contrast_ratios = {}
        z_order_issues = []
        
        try:
            # Create dry-run scene instance
            scene = scene_class()
            scene.render = lambda: None  # Disable actual rendering
            
            # Override self.play to capture animations
            captured_animations = []
            original_play = scene.play
            
            def capture_play(*args, **kwargs):
                captured_animations.extend(args)
                # Don't actually play - just capture
                return None
            
            scene.play = capture_play
            
            # Run construct to build scene
            scene.construct()
            
            # Analyze all objects in the scene
            all_objects = scene.mobjects
            
            # Sample animations at key points
            for alpha in self.config["sample_points"]:
                frame_patches = self._analyze_frame(all_objects, captured_animations, alpha)
                patches.extend(frame_patches)
            
            # Check overall composition
            composition_patches = self._analyze_composition(all_objects)
            patches.extend(composition_patches)
            
            # Collect bounding box data
            for obj in all_objects:
                if hasattr(obj, 'get_bounding_box'):
                    bbox = obj.get_bounding_box()
                    bounding_boxes[str(obj)] = bbox.tolist() if hasattr(bbox, 'tolist') else list(bbox)
            
        except Exception as e:
            patches.append(CriticPatch(
                issue_type="geometry_error",
                description=f"Geometry analysis failed: {str(e)}",
                code_edit="# Check scene construction for errors"
            ))
        
        return CriticReport(
            scene_name=scene_class_name,
            patches=patches,
            contrast_ratios=contrast_ratios,
            bounding_boxes=bounding_boxes,
            z_order_issues=z_order_issues
        )
    
    def _analyze_frame(self, objects: List[Any], animations: List[Any], alpha: float) -> List[CriticPatch]:
        """Analyze objects at a specific animation time point"""
        patches = []
        
        # Sample object positions at alpha
        object_states = []
        for obj in objects:
            try:
                # Simulate animation sampling
                if hasattr(obj, 'get_bounding_box'):
                    bbox = obj.get_bounding_box()
                    center = obj.get_center() if hasattr(obj, 'get_center') else [0, 0, 0]
                    object_states.append({
                        'object': obj,
                        'bbox': bbox,
                        'center': center,
                        'z_index': getattr(obj, 'z_index', 0)
                    })
            except:
                continue
        
        # Check for overlaps
        overlap_patches = self._check_overlaps(object_states, alpha)
        patches.extend(overlap_patches)
        
        # Check for off-screen objects
        offscreen_patches = self._check_offscreen(object_states, alpha)
        patches.extend(offscreen_patches)
        
        # Check for occlusion issues
        occlusion_patches = self._check_occlusion(object_states, alpha)
        patches.extend(occlusion_patches)
        
        return patches
    
    def _check_overlaps(self, object_states: List[Dict], alpha: float) -> List[CriticPatch]:
        """Check for object overlaps using bounding box intersection"""
        patches = []
        
        for i, state1 in enumerate(object_states):
            for j, state2 in enumerate(object_states[i+1:], i+1):
                try:
                    bbox1 = state1['bbox']
                    bbox2 = state2['bbox']
                    
                    # Calculate IoU (Intersection over Union)
                    iou = self._calculate_iou(bbox1, bbox2)
                    
                    if iou > self.config["overlap_threshold"]:
                        patches.append(CriticPatch(
                            issue_type="overlap",
                            description=f"Objects overlap significantly (IoU: {iou:.2f}) at t={alpha}",
                            code_edit=f"# Suggest: obj2.next_to(obj1, RIGHT, buff=1.0) or use arrange()"
                        ))
                except:
                    continue
        
        return patches
    
    def _check_offscreen(self, object_states: List[Dict], alpha: float) -> List[CriticPatch]:
        """Check if objects are positioned off-screen"""
        patches = []
        
        # Manim default frame boundaries (approximate)
        frame_width = 14.22  # FRAME_WIDTH
        frame_height = 8.0   # FRAME_HEIGHT
        
        for state in object_states:
            try:
                center = state['center']
                bbox = state['bbox']
                
                # Check if object extends beyond frame
                if (abs(center[0]) > frame_width/2 or 
                    abs(center[1]) > frame_height/2):
                    
                    patches.append(CriticPatch(
                        issue_type="off_screen",
                        description=f"Object positioned off-screen at t={alpha}",
                        code_edit="# Suggest: obj.scale_to_fit_width(config.frame_width * 0.8) or obj.to_edge()"
                    ))
            except:
                continue
        
        return patches
    
    def _check_occlusion(self, object_states: List[Dict], alpha: float) -> List[CriticPatch]:
        """Check for z-order occlusion issues"""
        patches = []
        
        # Sort by z-index (higher z is in front)
        sorted_states = sorted(object_states, key=lambda s: s.get('z_index', 0))
        
        for i, state in enumerate(sorted_states[:-1]):
            try:
                # Check if important content is hidden by objects in front
                for front_state in sorted_states[i+1:]:
                    if self._objects_overlap(state['bbox'], front_state['bbox']):
                        # Check if this is text being occluded
                        obj_type = type(state['object']).__name__
                        if 'Text' in obj_type or 'Tex' in obj_type:
                            patches.append(CriticPatch(
                                issue_type="occlusion",
                                description=f"Text object may be occluded at t={alpha}",
                                code_edit="# Suggest: text_obj.set_z_index(10) or rearrange layout"
                            ))
            except:
                continue
        
        return patches
    
    def _analyze_composition(self, objects: List[Any]) -> List[CriticPatch]:
        """Analyze overall scene composition"""
        patches = []
        
        # Check for contrast issues
        text_objects = []
        for obj in objects:
            obj_type = type(obj).__name__
            if 'Text' in obj_type or 'Tex' in obj_type:
                text_objects.append(obj)
        
        for text_obj in text_objects:
            try:
                # Get text color (simplified - actual implementation would be more complex)
                color = getattr(text_obj, 'color', '#FFFFFF')
                if hasattr(color, 'hex'):
                    color = color.hex
                elif hasattr(color, 'to_hex'):
                    color = color.to_hex()
                else:
                    color = '#FFFFFF'  # Default
                
                ratio = contrast_ratio(color, self.background_color)
                
                # Check WCAG requirements
                min_ratio = self.config["contrast_ratio_min"]
                if ratio < min_ratio:
                    patches.append(CriticPatch(
                        issue_type="low_contrast",
                        description=f"Text contrast ratio {ratio:.1f}:1 below WCAG minimum {min_ratio}:1",
                        code_edit="# Suggest: text.add_background_rectangle(opacity=0.8) or change color"
                    ))
            except:
                continue
        
        return patches
    
    def _calculate_iou(self, bbox1, bbox2) -> float:
        """Calculate Intersection over Union for two bounding boxes"""
        try:
            # Extract coordinates (assuming bbox format: [x_min, y_min, z_min, x_max, y_max, z_max])
            x1_min, y1_min = bbox1[0], bbox1[1]
            x1_max, y1_max = bbox1[3], bbox1[4]
            x2_min, y2_min = bbox2[0], bbox2[1]
            x2_max, y2_max = bbox2[3], bbox2[4]
            
            # Calculate intersection
            x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
            y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
            intersection = x_overlap * y_overlap
            
            # Calculate union
            area1 = (x1_max - x1_min) * (y1_max - y1_min)
            area2 = (x2_max - x2_min) * (y2_max - y2_min)
            union = area1 + area2 - intersection
            
            return intersection / union if union > 0 else 0
        except:
            return 0
    
    def _objects_overlap(self, bbox1, bbox2) -> bool:
        """Check if two bounding boxes overlap"""
        return self._calculate_iou(bbox1, bbox2) > 0
"""
Mock knowledge base for testing without requiring faiss and sentence-transformers.
Provides realistic Manim API knowledge for validation and code generation.
"""

import json
from typing import List, Dict, Any, Optional


class MockManimKnowledgeBase:
    """Mock knowledge base with essential Manim APIs"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.snippets = self._create_mock_snippets()
        print("MockManimKnowledgeBase initialized (no faiss required)")
    
    def _create_mock_snippets(self) -> List[Dict[str, Any]]:
        """Create essential Manim API snippets"""
        return [
            # Text objects
            {
                "id": "text_creation",
                "snippet": "Text('Hello World', font_size=48)",
                "category": "text",
                "notes": "Create text object with optional font size"
            },
            {
                "id": "text_positioning",
                "snippet": "text.to_edge(UP)",
                "category": "text",
                "notes": "Position text at edge of screen"
            },
            
            # Math objects
            {
                "id": "mathtex",
                "snippet": "MathTex(r'\\\\vec{F} = m\\\\vec{a}')",
                "category": "math",
                "notes": "Create mathematical expression with LaTeX"
            },
            {
                "id": "mathtex_scale",
                "snippet": "formula.scale(2)",
                "category": "math", 
                "notes": "Scale mathematical expression"
            },
            
            # Shapes
            {
                "id": "circle",
                "snippet": "Circle(radius=1, color=BLUE)",
                "category": "shapes",
                "notes": "Create circle with radius and color"
            },
            {
                "id": "rectangle",
                "snippet": "Rectangle(width=4, height=2)",
                "category": "shapes",
                "notes": "Create rectangle with dimensions"
            },
            
            # Animations
            {
                "id": "write_animation",
                "snippet": "self.play(Write(object), run_time=2)",
                "category": "animation",
                "notes": "Write animation with duration"
            },
            {
                "id": "fadein",
                "snippet": "self.play(FadeIn(object))",
                "category": "animation",
                "notes": "Fade in animation"
            },
            {
                "id": "transform",
                "snippet": "self.play(Transform(obj1, obj2))",
                "category": "animation",
                "notes": "Transform one object into another"
            },
            
            # Layout
            {
                "id": "next_to",
                "snippet": "obj2.next_to(obj1, DOWN)",
                "category": "layout",
                "notes": "Position object relative to another"
            },
            {
                "id": "arrange",
                "snippet": "VGroup(obj1, obj2).arrange(DOWN)",
                "category": "layout",
                "notes": "Arrange objects in a group"
            },
            
            # Plotting
            {
                "id": "axes",
                "snippet": "Axes(x_range=[-3, 3], y_range=[-3, 3])",
                "category": "plotting",
                "notes": "Create coordinate axes"
            },
            {
                "id": "function_graph",
                "snippet": "axes.plot(lambda x: x**2, color=RED)",
                "category": "plotting",
                "notes": "Plot function on axes"
            }
        ]
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Mock retrieval based on simple keyword matching"""
        if top_k is None:
            top_k = 5
            
        query_lower = query.lower()
        matches = []
        
        for snippet in self.snippets:
            # Simple keyword matching
            if any(word in snippet['snippet'].lower() or 
                   word in snippet['notes'].lower() or
                   word in snippet['category'].lower()
                   for word in query_lower.split()):
                matches.append(snippet)
        
        return matches[:top_k]
    
    def get_snippet_by_id(self, snippet_id: str) -> Optional[Dict[str, Any]]:
        """Get specific snippet by ID"""
        for snippet in self.snippets:
            if snippet['id'] == snippet_id:
                return snippet
        return None
    
    def get_all_snippets(self) -> List[Dict[str, Any]]:
        """Get all snippets in the knowledge base"""
        return self.snippets
    
    def add_snippet(self, snippet: Dict[str, Any]):
        """Add new snippet to knowledge base"""
        self.snippets.append(snippet)
"""
RAG (Retrieval-Augmented Generation) system for Manim knowledge base.
Uses FAISS for fast similarity search with embeddings.
"""

import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import toml

try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "Required packages not installed. Run: pip install faiss-cpu sentence-transformers"
    )


class ManimKnowledgeBase:
    """Manim code snippets and documentation knowledge base"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config = toml.load(config_path)["rag"]
        self.kb_dir = Path("kb")
        self.kb_dir.mkdir(exist_ok=True)
        
        self.snippets: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.Index] = None
        self.encoder = SentenceTransformer(self.config["embedding_model"])
        
        self._load_or_create_kb()
    
    def _load_or_create_kb(self):
        """Load existing KB or create from scratch"""
        snippets_file = self.kb_dir / "manim_snippets.json"
        embeddings_file = self.kb_dir / "embeddings.pkl"
        index_file = self.kb_dir / "faiss_index.bin"
        
        if all(f.exists() for f in [snippets_file, embeddings_file, index_file]):
            print("Loading existing knowledge base...")
            self._load_kb(snippets_file, embeddings_file, index_file)
        else:
            print("Creating new knowledge base...")
            self._create_kb()
            self._save_kb(snippets_file, embeddings_file, index_file)
    
    def _create_kb(self):
        """Create knowledge base with essential Manim snippets"""
        self.snippets = [
            {
                "id": "text_basic",
                "snippet": "Text('Hello World', font_size=48)",
                "notes": "Basic text object creation",
                "category": "text",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.text.text_mobject.Text.html"
            },
            {
                "id": "mathtex_basic", 
                "snippet": "MathTex(r'E = mc^2', font_size=48)",
                "notes": "Basic LaTeX math rendering",
                "category": "math",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.text.tex_mobject.MathTex.html"
            },
            {
                "id": "write_animation",
                "snippet": "self.play(Write(text_obj))",
                "notes": "Write animation for text/math objects",
                "category": "animation",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.creation.Write.html"
            },
            {
                "id": "fadein_animation",
                "snippet": "self.play(FadeIn(obj))",
                "notes": "Fade in any object",
                "category": "animation", 
                "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.fading.FadeIn.html"
            },
            {
                "id": "fadeout_animation",
                "snippet": "self.play(FadeOut(obj))",
                "notes": "Fade out any object",
                "category": "animation",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.fading.FadeOut.html"
            },
            {
                "id": "transform_animation",
                "snippet": "self.play(Transform(obj1, obj2))",
                "notes": "Transform one object into another",
                "category": "animation",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.transform.Transform.html"
            },
            {
                "id": "replacement_transform",
                "snippet": "self.play(ReplacementTransform(obj1, obj2))",
                "notes": "Replace one object with another (cleaner than Transform)",
                "category": "animation",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.animation.transform.ReplacementTransform.html"
            },
            {
                "id": "next_to_layout",
                "snippet": "obj2.next_to(obj1, RIGHT, buff=0.5)",
                "notes": "Position object relative to another",
                "category": "layout",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.mobject.Mobject.html#manim.mobject.mobject.Mobject.next_to"
            },
            {
                "id": "arrange_layout",
                "snippet": "VGroup(obj1, obj2, obj3).arrange(RIGHT, buff=1)",
                "notes": "Arrange multiple objects in a row/column",
                "category": "layout",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.mobject.Mobject.html#manim.mobject.mobject.Mobject.arrange"
            },
            {
                "id": "to_edge_layout",
                "snippet": "obj.to_edge(UP)",
                "notes": "Move object to screen edge",
                "category": "layout",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.mobject.Mobject.html#manim.mobject.mobject.Mobject.to_edge"
            },
            {
                "id": "axes_basic",
                "snippet": "Axes(x_range=[-3, 3], y_range=[-2, 2], x_length=6, y_length=4)",
                "notes": "Basic coordinate axes",
                "category": "plotting",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.coordinate_systems.Axes.html"
            },
            {
                "id": "axes_plot",
                "snippet": "graph = axes.plot(lambda x: x**2, color=BLUE)",
                "notes": "Plot function on axes",
                "category": "plotting", 
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.coordinate_systems.Axes.html#manim.mobject.graphing.coordinate_systems.Axes.plot"
            },
            {
                "id": "axes_labels",
                "snippet": "labels = axes.get_axis_labels(x_label='x', y_label='y')",
                "notes": "Add axis labels",
                "category": "plotting",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.graphing.coordinate_systems.Axes.html#manim.mobject.graphing.coordinate_systems.Axes.get_axis_labels"
            },
            {
                "id": "vgroup_basic",
                "snippet": "group = VGroup(obj1, obj2, obj3)",
                "notes": "Group objects together for collective operations",
                "category": "grouping",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.types.vectorized_mobject.VGroup.html"
            },
            {
                "id": "circle_basic",
                "snippet": "Circle(radius=1, color=BLUE)",
                "notes": "Basic circle shape",
                "category": "shapes",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.arc.Circle.html"
            },
            {
                "id": "rectangle_basic",
                "snippet": "Rectangle(width=4, height=2, color=RED)",
                "notes": "Basic rectangle shape", 
                "category": "shapes",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.polygram.Rectangle.html"
            },
            {
                "id": "line_basic",
                "snippet": "Line(start=LEFT, end=RIGHT, color=WHITE)",
                "notes": "Basic line between two points",
                "category": "shapes",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.line.Line.html"
            },
            {
                "id": "arrow_basic",
                "snippet": "Arrow(start=LEFT, end=RIGHT, color=YELLOW)",
                "notes": "Basic arrow",
                "category": "shapes",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.geometry.line.Arrow.html"
            },
            {
                "id": "vector_field",
                "snippet": "VectorField(lambda pos: np.array([pos[1], -pos[0], 0]))",
                "notes": "Vector field visualization",
                "category": "physics",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.vector_field.VectorField.html"
            },
            {
                "id": "always_redraw",
                "snippet": "always_redraw(lambda: Line(dot1.get_center(), dot2.get_center()))",
                "notes": "Create objects that update automatically",
                "category": "dynamic",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.mobject.Mobject.html#manim.mobject.mobject.Mobject.add_updater"
            },
            {
                "id": "value_tracker",
                "snippet": "tracker = ValueTracker(0); tracker.animate.set_value(5)",
                "notes": "Track numeric values for animations",
                "category": "dynamic",
                "source_url": "https://docs.manim.community/en/stable/reference/manim.mobject.value_tracker.ValueTracker.html"
            }
        ]
        
        # Generate embeddings
        texts = [f"{s['snippet']} {s['notes']}" for s in self.snippets]
        self.embeddings = self.encoder.encode(texts)
        
        # Create FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)
    
    def _load_kb(self, snippets_file: Path, embeddings_file: Path, index_file: Path):
        """Load existing knowledge base"""
        with open(snippets_file) as f:
            self.snippets = json.load(f)
        
        with open(embeddings_file, 'rb') as f:
            self.embeddings = pickle.load(f)
        
        self.index = faiss.read_index(str(index_file))
    
    def _save_kb(self, snippets_file: Path, embeddings_file: Path, index_file: Path):
        """Save knowledge base to disk"""
        with open(snippets_file, 'w') as f:
            json.dump(self.snippets, f, indent=2)
        
        with open(embeddings_file, 'wb') as f:
            pickle.dump(self.embeddings, f)
        
        faiss.write_index(self.index, str(index_file))
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant snippets for a query"""
        if top_k is None:
            top_k = self.config["top_k"]
        
        # Encode query
        query_embedding = self.encoder.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search index
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Filter by minimum similarity
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= self.config["min_similarity"]:
                snippet = self.snippets[idx].copy()
                snippet["similarity"] = float(score)
                results.append(snippet)
        
        return results
    
    def get_snippet_by_id(self, snippet_id: str) -> Optional[Dict[str, Any]]:
        """Get specific snippet by ID"""
        for snippet in self.snippets:
            if snippet["id"] == snippet_id:
                return snippet
        return None
    
    def get_all_snippets(self) -> List[Dict[str, Any]]:
        """Get all snippets in the knowledge base"""
        return self.snippets.copy()
    
    def add_snippet(self, snippet: Dict[str, Any]):
        """Add new snippet to knowledge base"""
        # Generate embedding
        text = f"{snippet['snippet']} {snippet['notes']}"
        embedding = self.encoder.encode([text])
        faiss.normalize_L2(embedding)
        
        # Add to collections
        self.snippets.append(snippet)
        if self.embeddings is None:
            self.embeddings = embedding
        else:
            self.embeddings = np.vstack([self.embeddings, embedding])
        
        # Update index
        self.index.add(embedding)
        
        # Save updated KB
        self._save_kb(
            self.kb_dir / "manim_snippets.json",
            self.kb_dir / "embeddings.pkl", 
            self.kb_dir / "faiss_index.bin"
        )
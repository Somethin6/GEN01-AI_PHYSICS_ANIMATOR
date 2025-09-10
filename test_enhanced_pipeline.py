#!/usr/bin/env python3
"""
Test the enhanced pipeline generation (without rendering)
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from engine.preflight import preflight_check
from engine.enhanced_pipeline import run_enhanced_pipeline
from rich import print
from rich.console import Console

console = Console()

def main():
    """Test enhanced pipeline generation for fourier transform"""
    
    # Mock environment for testing
    env = {
        "cfg": {
            "llm": {
                "host": "http://127.0.0.1:11434",
                "model": "qwen2.5:14b-instruct-q4_K_M",
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 2048,
                "stop": []
            },
            "target_duration_s": 15
        },
        "tools": {
            "latex_ok": False  # Use Text fallback for now
        }
    }
    
    topic = "fourier transform"
    
    console.print(f"[bold cyan]Testing Enhanced Pipeline: {topic}[/bold cyan]")
    
    try:
        # Run the enhanced pipeline
        code = run_enhanced_pipeline(topic, env)
        
        # Save the generated code
        output_path = Path("generated_fourier_code.py")
        output_path.write_text(code, encoding="utf-8")
        
        console.print(f"[bold green]SUCCESS![/bold green]")
        console.print(f"Generated code saved to: {output_path}")
        console.print("\n[bold]Generated Code Preview:[/bold]")
        
        # Show first 50 lines
        lines = code.split('\n')
        preview_lines = lines[:50]
        if len(lines) > 50:
            preview_lines.append("... (truncated)")
        
        for i, line in enumerate(preview_lines, 1):
            console.print(f"{i:3d}: {line}")
            
        return 0
        
    except Exception as e:
        console.print(f"[red]ERROR: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

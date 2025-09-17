"""
In-process LLM engine using llama-cpp-python with GPU acceleration.
Optimized for 2080 Ti with high tok/s performance.
"""

import json
import time
import toml
from pathlib import Path
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel

try:
    from llama_cpp import Llama, GGMLType
except ImportError:
    raise ImportError(
        "llama-cpp-python not installed. Run: pip install llama-cpp-python[server]"
    )


class LLMEngine:
    """High-performance in-process LLM with structured JSON generation"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config = toml.load(config_path)["llm"]
        self.perf_config = toml.load(config_path)["performance"]
        self.llm: Optional[Llama] = None
        self.prompt_cache: Dict[str, Any] = {}  # For caching repeated prompts
        self.total_tokens_generated = 0
        self.total_generation_time = 0.0
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize Llama model with optimized settings"""
        model_path = self.config["model_path"]
        
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}\n"
                f"Download a GGUF model to {model_path}"
            )
        
        # Map string type names to GGMLType enums
        type_map = {
            "Q4_0": GGMLType.Q4_0,
            "Q4_1": GGMLType.Q4_1, 
            "Q5_0": GGMLType.Q5_0,
            "Q5_1": GGMLType.Q5_1,
            "Q8_0": GGMLType.Q8_0,
            "Q8_1": GGMLType.Q8_1,
            "F16": GGMLType.F16,
            "F32": GGMLType.F32,
        }
        
        type_k = type_map.get(self.config["type_k"], GGMLType.Q8_0)
        type_v = type_map.get(self.config["type_v"], GGMLType.Q8_0)
        
        print(f"Loading model: {model_path}")
        print(f"GPU layers: {self.config['n_gpu_layers']}")
        print(f"Batch size: {self.config['n_batch']}")
        print(f"KV cache quant: {self.config['type_k']}/{self.config['type_v']}")
        
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=self.config["n_gpu_layers"],
            n_ctx=self.config["n_ctx"],
            n_batch=self.config["n_batch"],
            n_ubatch=self.config["n_ubatch"],
            offload_kqv=self.config["offload_kqv"],
            flash_attn=self.config["flash_attn"],
            type_k=type_k,
            type_v=type_v,
            chat_format=self.config["chat_format"],
            verbose=self.config["verbose"],
        )
        
        print("Model loaded successfully!")
        self._benchmark_performance()
        
    def _benchmark_performance(self):
        """Benchmark token generation performance"""
        print("Benchmarking performance...")
        
        start_time = time.time()
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Generate exactly 100 words about physics."}
            ],
            max_tokens=self.perf_config["benchmark_tokens"],
            temperature=0.1,
        )
        end_time = time.time()
        
        duration = end_time - start_time
        tokens = self.perf_config["benchmark_tokens"]
        tok_per_sec = tokens / duration
        
        print(f"Performance: {tok_per_sec:.1f} tok/s ({tokens} tokens in {duration:.1f}s)")
        
        if tok_per_sec < self.perf_config["target_tokens_per_second"]:
            print(f"WARNING: Performance below target {self.perf_config['target_tokens_per_second']} tok/s")
            print("Consider adjusting n_batch, n_ubatch, or KV cache quantization")
    
    def generate_structured(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        schema: Type[BaseModel],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        use_cache: bool = True
    ) -> BaseModel:
        """Generate structured output matching Pydantic schema"""
        
        # Check cache first
        cache_key = self._get_cache_key(system_prompt, user_prompt, temperature)
        if use_cache and cache_key in self.prompt_cache:
            cached_result = self.prompt_cache[cache_key]
            try:
                return schema.model_validate(cached_result)
            except AttributeError:
                return schema.parse_obj(cached_result)
        
        # Fix for different pydantic versions
        try:
            json_schema = schema.model_json_schema()
        except AttributeError:
            json_schema = schema.schema()  # Pydantic v1

        # Add schema instruction to system prompt
        enhanced_system = f"""{system_prompt}

You must respond with valid JSON that matches this exact schema:
{json.dumps(json_schema, indent=2)}

Only return the JSON object, no other text."""

        start_time = time.time()
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": enhanced_system},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={
                "type": "json_object",
                "schema": json_schema
            }
        )
        end_time = time.time()
        
        # Track performance
        generation_time = end_time - start_time
        self._track_generation(max_tokens, generation_time)
        
        content = response["choices"][0]["message"]["content"]
        
        try:
            # Parse JSON and validate with schema
            data = json.loads(content)
            
            # Cache successful result
            if use_cache:
                self.prompt_cache[cache_key] = data
            
            # Fix for different pydantic versions  
            try:
                return schema.model_validate(data)
            except AttributeError:
                return schema.parse_obj(data)  # Pydantic v1
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse structured response: {e}\nContent: {content}")
    
    def generate_text(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> str:
        """Generate plain text response"""
        
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return response["choices"][0]["message"]["content"]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        if not self.llm:
            return {}
            
        avg_tok_per_sec = 0.0
        if self.total_generation_time > 0:
            avg_tok_per_sec = self.total_tokens_generated / self.total_generation_time
            
        return {
            "model_loaded": True,
            "context_size": self.config["n_ctx"],
            "batch_size": self.config["n_batch"],
            "gpu_layers": self.config["n_gpu_layers"],
            "total_tokens_generated": self.total_tokens_generated,
            "total_generation_time": self.total_generation_time,
            "average_tokens_per_second": avg_tok_per_sec,
            "cache_size": len(self.prompt_cache),
        }
        
    def clear_cache(self):
        """Clear the prompt cache"""
        self.prompt_cache.clear()
        
    def _get_cache_key(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """Generate cache key for prompt caching"""
        import hashlib
        content = f"{system_prompt}|{user_prompt}|{temperature}"
        return hashlib.md5(content.encode()).hexdigest()
        
    def _track_generation(self, tokens: int, duration: float):
        """Track token generation statistics"""
        self.total_tokens_generated += tokens
        self.total_generation_time += duration
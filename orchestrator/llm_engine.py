"""
In-process LLM engine using llama-cpp-python with GPU acceleration.
Optimized for 2080 Ti with high tok/s performance.
"""

import json
import time
import toml
from pathlib import Path
from typing import Dict, Any, Optional, Type, Union
from pydantic import BaseModel

try:
    from llama_cpp import Llama, GGMLType
    LLAMA_CPP_AVAILABLE = True
    try:
        from llama_cpp.llama_speculative import LlamaPromptLookupDecoding
        SPECULATIVE_AVAILABLE = True
    except ImportError:
        # Fallback for older versions or different module structure
        LlamaPromptLookupDecoding = None
        SPECULATIVE_AVAILABLE = False
    try:
        from llama_cpp.llama_grammar import LlamaGrammar
        GRAMMAR_AVAILABLE = True
    except ImportError:
        # Fallback for older versions or different module structure
        LlamaGrammar = None
        GRAMMAR_AVAILABLE = False
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    SPECULATIVE_AVAILABLE = False
    GRAMMAR_AVAILABLE = False
    LlamaPromptLookupDecoding = None
    LlamaGrammar = None
    
    # Only raise error if actually trying to use the engine
    class MockLlama:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "llama-cpp-python not installed. Run: pip install llama-cpp-python[server]"
            )
    
    Llama = MockLlama
    GGMLType = None


class LLMEngine:
    """High-performance in-process LLM with structured JSON generation"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config = toml.load(config_path)["llm"]
        self.perf_config = toml.load(config_path)["performance"]
        self.llm: Optional[Llama] = None
        self.draft_model: Optional[Llama] = None
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
        if GGMLType:
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
        else:
            # Fallback for when GGMLType is not available
            type_k = self.config.get("type_k", "Q8_0")
            type_v = self.config.get("type_v", "Q8_0")
        
        print(f"Loading model: {model_path}")
        print(f"GPU layers: {self.config['n_gpu_layers']}")
        print(f"Batch size: {self.config['n_batch']}")
        print(f"KV cache quant: {self.config['type_k']}/{self.config['type_v']}")
        
        # Initialize speculative decoding if enabled
        draft_model_config = None
        if self.config.get("enable_speculative_decoding", True) and SPECULATIVE_AVAILABLE:
            if self.config.get("draft_model_path"):
                print("Loading draft model for speculative decoding...")
                self.draft_model = Llama(
                    model_path=self.config["draft_model_path"],
                    n_gpu_layers=self.config.get("draft_gpu_layers", -1),
                    n_ctx=self.config["n_ctx"],
                    verbose=False
                )
                draft_model_config = self.draft_model
            else:
                print("Using prompt lookup decoding (no draft model)")
                draft_model_config = LlamaPromptLookupDecoding(
                    num_pred_tokens=self.config.get("speculative_tokens", 2)
                )
        elif self.config.get("enable_speculative_decoding", True):
            print("Speculative decoding requested but not available in this llama-cpp-python version")
        
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=self.config["n_gpu_layers"],
            n_ctx=self.config["n_ctx"],
            n_batch=self.config["n_batch"],
            n_ubatch=self.config["n_ubatch"],
            n_threads=self.config.get("n_threads", 12),
            offload_kqv=self.config["offload_kqv"],
            flash_attn=self.config["flash_attn"],
            type_k=type_k,
            type_v=type_v,
            chat_format=self.config["chat_format"],
            verbose=self.config["verbose"],
            draft_model=draft_model_config,
            rope_freq_base=self.config.get("rope_freq_base", 0.0),
            rope_freq_scale=self.config.get("rope_freq_scale", 0.0),
            numa=self.config.get("numa", False),
            seed=self.config.get("seed", 42),  # Deterministic by default
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
        use_cache: bool = True,
        use_grammar: bool = False,
        repeat_penalty: float = 1.05
    ) -> BaseModel:
        """Generate structured output matching Pydantic schema with optional GBNF grammar"""
        
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

        # Create grammar from schema if requested
        grammar = None
        if use_grammar:
            grammar = self._create_gbnf_grammar(json_schema)

        # Add schema instruction to system prompt
        enhanced_system = f"""{system_prompt}

You must respond with valid JSON that matches this exact schema:
{json.dumps(json_schema, indent=2)}

Only return the JSON object, no other text."""

        start_time = time.time()
        
        completion_kwargs = {
            "messages": [
                {"role": "system", "content": enhanced_system},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": self.config.get("top_p", 0.9),
            "repeat_penalty": repeat_penalty,
        }
        
        # Add grammar or JSON schema constraint
        if grammar:
            completion_kwargs["grammar"] = grammar
        else:
            completion_kwargs["response_format"] = {
                "type": "json_object",
                "schema": json_schema
            }
        
        response = self.llm.create_chat_completion(**completion_kwargs)
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
    
    def _create_gbnf_grammar(self, json_schema: Dict[str, Any]) -> Optional[Any]:
        """Create GBNF grammar from JSON schema"""
        if not GRAMMAR_AVAILABLE:
            print("Warning: GBNF grammar not available in this llama-cpp-python version")
            return None
            
        # Basic GBNF grammar for JSON - can be enhanced based on schema
        json_grammar = r'''
        root  ::= object
        value ::= object | array | string | number | ("true" | "false" | "null") ws
        
        object ::=
          "{" ws (
                string ":" ws value
                ("," ws string ":" ws value)*
              )? "}" ws
        
        array  ::=
          "[" ws (
                value
                ("," ws value)*
              )? "]" ws
        
        string ::=
          "\"" (
            [^"\\] |
            "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])
          )* "\"" ws
        
        number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws
        
        ws ::= [ \t\n]*
        '''
        
        try:
            return LlamaGrammar.from_string(json_grammar)
        except Exception as e:
            print(f"Warning: Could not create GBNF grammar: {e}")
            return None
    
    def generate_with_retries(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel] = None,
        max_retries: int = 3,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        use_grammar: bool = False
    ) -> Union[BaseModel, str]:
        """Generate with automatic retries on failure"""
        
        last_error = None
        for attempt in range(max_retries):
            try:
                if schema:
                    return self.generate_structured(
                        system_prompt, user_prompt, schema, temperature, max_tokens, 
                        use_grammar=use_grammar
                    )
                else:
                    return self.generate_text(system_prompt, user_prompt, temperature, max_tokens)
                    
            except Exception as e:
                last_error = e
                print(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    # Slightly increase temperature for retry
                    temperature = min(temperature + 0.1, 0.8)
        
        raise ValueError(f"Failed after {max_retries} attempts. Last error: {last_error}")
    
    def warm_up_model(self):
        """Warm up model with small generation to optimize performance"""
        print("Warming up model...")
        try:
            self.generate_text(
                "You are a helpful assistant.",
                "Say hello.",
                temperature=0.1,
                max_tokens=10
            )
            print("Model warmed up successfully")
        except Exception as e:
            print(f"Warning: Model warm-up failed: {e}")
    
    def estimate_vram_usage(self) -> Dict[str, float]:
        """Estimate VRAM usage breakdown"""
        # This is a rough estimation based on typical patterns
        model_size_gb = 8.5  # Typical for 14B Q4_K_M model
        
        # Context and batch scaling
        ctx_size_mb = (self.config["n_ctx"] * 4 * 2) / 1024 / 1024  # Rough estimate
        batch_mb = (self.config["n_batch"] * 4) / 1024 / 1024
        
        # KV cache scaling based on quantization
        kv_multiplier = 0.5 if self.config["type_k"] == "Q4_0" else 1.0
        kv_cache_mb = ctx_size_mb * kv_multiplier
        
        total_estimate = (model_size_gb * 1024) + ctx_size_mb + batch_mb + kv_cache_mb
        
        return {
            "model_gb": model_size_gb,
            "context_mb": ctx_size_mb,
            "batch_mb": batch_mb,
            "kv_cache_mb": kv_cache_mb,
            "total_estimated_mb": total_estimate,
            "headroom_mb": 11264 - total_estimate,  # 2080 Ti total - estimate
        }
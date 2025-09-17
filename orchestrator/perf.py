"""
Performance measurement and optimization for LLM inference.
Benchmarks different configurations and finds optimal settings for 2080 Ti.
"""

import time
import json
import psutil
import toml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

try:
    import GPUtil
except ImportError:
    GPUtil = None

from orchestrator.llm_engine import LLMEngine


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark run"""
    config: Dict[str, Any]
    tokens_per_second: float
    prefill_time: float
    decode_time: float
    total_time: float
    memory_usage_mb: float
    gpu_memory_mb: Optional[float]
    success: bool
    error: Optional[str] = None


class PerformanceTuner:
    """Automatically tune LLM performance for optimal tok/s"""
    
    def __init__(self, config_path: str = "orchestrator/config.toml"):
        self.config_path = config_path
        self.config = toml.load(config_path)
        self.benchmark_tokens = self.config["performance"]["benchmark_tokens"]
        self.target_tokens_per_second = self.config["performance"]["target_tokens_per_second"]
        self.vram_headroom_gb = self.config["performance"]["vram_headroom_gb"]
        
    def benchmark_current_config(self) -> BenchmarkResult:
        """Benchmark the current configuration"""
        
        print("Benchmarking current configuration...")
        
        try:
            # Initialize engine with current config
            engine = LLMEngine(self.config_path)
            
            # Measure memory before test
            initial_memory = self._get_memory_usage()
            
            # Run benchmark
            start_time = time.time()
            
            system_prompt = "You are a helpful assistant that explains physics concepts clearly."
            user_prompt = f"Explain quantum mechanics in exactly {self.benchmark_tokens//4} words."
            
            response = engine.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.benchmark_tokens,
                temperature=0.1
            )
            
            end_time = time.time()
            
            # Calculate metrics
            total_time = end_time - start_time
            tokens_generated = len(response.split()) * 1.3  # Approximate token count
            tokens_per_second = tokens_generated / total_time
            
            # Measure memory after test
            final_memory = self._get_memory_usage()
            
            return BenchmarkResult(
                config=self.config["llm"].copy(),
                tokens_per_second=tokens_per_second,
                prefill_time=total_time * 0.1,  # Estimate
                decode_time=total_time * 0.9,   # Estimate
                total_time=total_time,
                memory_usage_mb=final_memory["ram_mb"] - initial_memory["ram_mb"],
                gpu_memory_mb=final_memory.get("gpu_mb"),
                success=True
            )
            
        except Exception as e:
            return BenchmarkResult(
                config=self.config["llm"].copy(),
                tokens_per_second=0.0,
                prefill_time=0.0,
                decode_time=0.0,
                total_time=0.0,
                memory_usage_mb=0.0,
                gpu_memory_mb=None,
                success=False,
                error=str(e)
            )
    
    def sweep_configurations(self) -> List[BenchmarkResult]:
        """Sweep through different configurations to find optimal settings"""
        
        print("Starting configuration sweep...")
        
        # Parameter ranges to test
        batch_sizes = [256, 512, 1024, 2048]
        ubatch_sizes = [128, 256, 512]
        kv_quant_types = ["Q8_0", "Q4_0", "F16"]
        
        results = []
        base_config = self.config["llm"].copy()
        
        for n_batch in batch_sizes:
            for n_ubatch in ubatch_sizes:
                if n_ubatch > n_batch:
                    continue  # Skip invalid combinations
                    
                for type_kv in kv_quant_types:
                    # Update config for this test
                    test_config = base_config.copy()
                    test_config.update({
                        "n_batch": n_batch,
                        "n_ubatch": n_ubatch,
                        "type_k": type_kv,
                        "type_v": type_kv
                    })
                    
                    print(f"Testing: batch={n_batch}, ubatch={n_ubatch}, kv_quant={type_kv}")
                    
                    # Write temporary config
                    self._write_temp_config(test_config)
                    
                    # Benchmark this configuration
                    result = self.benchmark_current_config()
                    result.config = test_config
                    results.append(result)
                    
                    # Print immediate results
                    if result.success:
                        print(f"  Result: {result.tokens_per_second:.1f} tok/s")
                    else:
                        print(f"  Failed: {result.error}")
                    
                    # Stop if we hit memory limits
                    if result.gpu_memory_mb and result.gpu_memory_mb > 8000:  # Approaching 2080 Ti limit
                        print("  Approaching GPU memory limit, skipping larger configs")
                        break
        
        # Restore original config
        self._write_temp_config(base_config)
        
        return results
    
    def find_optimal_config(self) -> Dict[str, Any]:
        """Find the optimal configuration for maximum performance"""
        
        print("Finding optimal configuration...")
        
        # Run sweep
        results = self.sweep_configurations()
        
        # Filter successful results
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            print("No successful configurations found!")
            return self.config["llm"]
        
        # Sort by tokens per second
        successful_results.sort(key=lambda r: r.tokens_per_second, reverse=True)
        
        # Print top results
        print("\nTop 5 configurations:")
        for i, result in enumerate(successful_results[:5]):
            print(f"{i+1}. {result.tokens_per_second:.1f} tok/s - batch={result.config['n_batch']}, ubatch={result.config['n_ubatch']}, kv_quant={result.config['type_k']}")
        
        # Select best configuration that meets constraints
        best_config = None
        for result in successful_results:
            # Check if it meets our constraints
            meets_target = result.tokens_per_second >= self.target_tokens_per_second
            within_memory = (not result.gpu_memory_mb or 
                           result.gpu_memory_mb <= (8192 - self.vram_headroom_gb * 1024))
            
            if meets_target and within_memory:
                best_config = result.config
                print(f"\nOptimal config found: {result.tokens_per_second:.1f} tok/s")
                break
        
        if not best_config:
            # Fall back to fastest config even if it doesn't meet all constraints
            best_config = successful_results[0].config
            print(f"\nUsing fastest config (may exceed constraints): {successful_results[0].tokens_per_second:.1f} tok/s")
        
        return best_config
    
    def auto_tune(self) -> bool:
        """Automatically tune and save optimal configuration"""
        
        print("Starting automatic performance tuning...")
        
        # Find optimal config
        optimal_config = self.find_optimal_config()
        
        # Update main config file
        self.config["llm"] = optimal_config
        
        with open(self.config_path, 'w') as f:
            toml.dump(self.config, f)
        
        print(f"Optimal configuration saved to {self.config_path}")
        
        # Verify the new configuration works
        print("Verifying new configuration...")
        final_result = self.benchmark_current_config()
        
        if final_result.success:
            print(f"Verification successful: {final_result.tokens_per_second:.1f} tok/s")
            return True
        else:
            print(f"Verification failed: {final_result.error}")
            return False
    
    def _write_temp_config(self, llm_config: Dict[str, Any]):
        """Write temporary configuration for testing"""
        temp_config = self.config.copy()
        temp_config["llm"] = llm_config
        
        with open(self.config_path, 'w') as f:
            toml.dump(temp_config, f)
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage stats"""
        
        # RAM usage
        ram_usage = psutil.virtual_memory()
        
        result = {
            "ram_mb": ram_usage.used / 1024 / 1024,
            "ram_percent": ram_usage.percent
        }
        
        # GPU memory if available
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # First GPU
                    result["gpu_mb"] = gpu.memoryUsed
                    result["gpu_percent"] = gpu.memoryUtil * 100
            except:
                pass
        
        return result
    
    def save_benchmark_report(self, results: List[BenchmarkResult], output_file: str = "benchmark_report.json"):
        """Save detailed benchmark report"""
        
        report = {
            "timestamp": time.time(),
            "system_info": self._get_system_info(),
            "target_performance": {
                "tokens_per_second": self.target_tokens_per_second,
                "benchmark_tokens": self.benchmark_tokens
            },
            "results": []
        }
        
        for result in results:
            report["results"].append({
                "config": result.config,
                "performance": {
                    "tokens_per_second": result.tokens_per_second,
                    "total_time": result.total_time,
                    "prefill_time": result.prefill_time,
                    "decode_time": result.decode_time
                },
                "memory": {
                    "ram_mb": result.memory_usage_mb,
                    "gpu_mb": result.gpu_memory_mb
                },
                "success": result.success,
                "error": result.error
            })
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Benchmark report saved to {output_file}")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for the report"""
        
        info = {
            "cpu_count": psutil.cpu_count(),
            "ram_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "platform": psutil.platform.platform()
        }
        
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    info["gpu"] = {
                        "name": gpu.name,
                        "memory_total_mb": gpu.memoryTotal,
                        "driver": gpu.driver
                    }
            except:
                pass
        
        return info


def main():
    """Command-line interface for performance tuning"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Performance Tuner")
    parser.add_argument("--benchmark", action="store_true", help="Benchmark current config")
    parser.add_argument("--sweep", action="store_true", help="Sweep configurations")
    parser.add_argument("--auto-tune", action="store_true", help="Auto-tune for optimal performance")
    parser.add_argument("--config", default="orchestrator/config.toml", help="Config file path")
    
    args = parser.parse_args()
    
    tuner = PerformanceTuner(args.config)
    
    if args.benchmark:
        result = tuner.benchmark_current_config()
        print(f"Performance: {result.tokens_per_second:.1f} tok/s")
        
    elif args.sweep:
        results = tuner.sweep_configurations()
        tuner.save_benchmark_report(results)
        
    elif args.auto_tune:
        success = tuner.auto_tune()
        if success:
            print("Auto-tuning completed successfully!")
        else:
            print("Auto-tuning failed!")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
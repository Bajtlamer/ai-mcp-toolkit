"""GPU monitoring and optimization utilities for AI MCP Toolkit."""

import asyncio
import subprocess
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class GPUInfo:
    """GPU information and status."""
    gpu_id: int
    name: str
    memory_total: int  # MB
    memory_used: int   # MB
    memory_free: int   # MB
    utilization: int   # Percentage
    temperature: int   # Celsius
    power_usage: int   # Watts
    driver_version: str


@dataclass  
class OllamaGPUStatus:
    """Ollama GPU usage status."""
    model_name: str
    model_size: str
    processor: str
    gpu_memory_used: int  # MB
    is_gpu_accelerated: bool
    context_length: int


@dataclass
class PerformanceMetrics:
    """Performance metrics for GPU operations."""
    timestamp: float = field(default_factory=time.time)
    gpu_utilization: float = 0.0
    gpu_memory_usage: float = 0.0
    ollama_memory_usage: int = 0
    inference_speed: float = 0.0  # tokens/second
    model_load_time: float = 0.0  # seconds
    request_count: int = 0
    total_tokens_processed: int = 0
    average_response_time: float = 0.0


class GPUMonitor:
    """Monitor GPU performance and Ollama usage."""
    
    def __init__(self):
        """Initialize GPU monitor."""
        self.logger = get_logger(self.__class__.__name__)
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self.current_metrics = PerformanceMetrics()
        
    async def start_monitoring(self, interval: float = 5.0) -> None:
        """Start continuous GPU monitoring."""
        if self._monitoring:
            self.logger.warning("GPU monitoring already started")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        self.logger.info(f"Started GPU monitoring with {interval}s interval")
    
    async def stop_monitoring(self) -> None:
        """Stop continuous GPU monitoring."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped GPU monitoring")
    
    async def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self.update_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def update_metrics(self) -> PerformanceMetrics:
        """Update current performance metrics."""
        try:
            # Get GPU info
            gpu_info = await self.get_gpu_info()
            
            # Get Ollama status
            ollama_status = await self.get_ollama_gpu_status()
            
            # Update current metrics
            self.current_metrics = PerformanceMetrics(
                timestamp=time.time(),
                gpu_utilization=gpu_info.utilization if gpu_info else 0.0,
                gpu_memory_usage=(gpu_info.memory_used / gpu_info.memory_total * 100) if gpu_info else 0.0,
                ollama_memory_usage=ollama_status.gpu_memory_used if ollama_status else 0,
            )
            
            # Add to history
            self.metrics_history.append(self.current_metrics)
            
            # Limit history size
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            return self.current_metrics
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
            return self.current_metrics
    
    async def get_gpu_info(self) -> Optional[GPUInfo]:
        """Get detailed GPU information using nvidia-smi."""
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,driver_version",
                "--format=csv,noheader,nounits"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(f"nvidia-smi failed: {stderr.decode()}")
                return None
            
            lines = stdout.decode().strip().split('\n')
            if not lines:
                return None
            
            # Parse first GPU (index 0)
            parts = [part.strip() for part in lines[0].split(',')]
            if len(parts) >= 9:
                return GPUInfo(
                    gpu_id=int(parts[0]),
                    name=parts[1],
                    memory_total=int(parts[2]),
                    memory_used=int(parts[3]),
                    memory_free=int(parts[4]),
                    utilization=int(parts[5]),
                    temperature=int(parts[6]),
                    power_usage=int(float(parts[7])),
                    driver_version=parts[8]
                )
            
        except Exception as e:
            self.logger.debug(f"Could not get GPU info: {e}")
            return None
    
    async def get_ollama_gpu_status(self) -> Optional[OllamaGPUStatus]:
        """Get Ollama GPU usage status."""
        try:
            cmd = ["ollama", "ps"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.debug(f"ollama ps failed: {stderr.decode()}")
                return None
            
            output = stdout.decode().strip()
            lines = output.split('\n')
            
            # Skip header line and look for active models
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    model_name = parts[0]
                    model_size = parts[2]
                    processor = " ".join(parts[3:-2])  # Handle multi-word processor info
                    
                    # Extract GPU memory usage from size
                    gpu_memory = 0
                    if "GB" in model_size:
                        gpu_memory = int(float(model_size.replace("GB", "")) * 1024)
                    elif "MB" in model_size:
                        gpu_memory = int(model_size.replace("MB", ""))
                    
                    return OllamaGPUStatus(
                        model_name=model_name,
                        model_size=model_size,
                        processor=processor,
                        gpu_memory_used=gpu_memory,
                        is_gpu_accelerated="GPU" in processor,
                        context_length=int(parts[-2]) if parts[-2].isdigit() else 4096
                    )
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not get Ollama status: {e}")
            return None
    
    async def get_optimization_recommendations(self) -> List[str]:
        """Get GPU optimization recommendations based on current status."""
        recommendations = []
        
        try:
            gpu_info = await self.get_gpu_info()
            ollama_status = await self.get_ollama_gpu_status()
            
            if not gpu_info:
                recommendations.append("⚠️  GPU monitoring unavailable - check NVIDIA drivers")
                return recommendations
            
            # Memory usage recommendations
            memory_usage_percent = (gpu_info.memory_used / gpu_info.memory_total) * 100
            
            if memory_usage_percent < 30:
                recommendations.append("💡 GPU memory usage is low - consider using a larger model for better quality")
            elif memory_usage_percent > 90:
                recommendations.append("⚠️  GPU memory usage is high - consider using a smaller model to prevent OOM errors")
            
            # Temperature recommendations
            if gpu_info.temperature > 80:
                recommendations.append("🌡️  GPU temperature is high - check cooling and consider reducing workload")
            elif gpu_info.temperature < 40:
                recommendations.append("❄️  GPU temperature is optimal for sustained workloads")
            
            # Utilization recommendations
            if gpu_info.utilization < 50:
                recommendations.append("⚡ GPU utilization is low - batch processing could improve efficiency")
            elif gpu_info.utilization > 95:
                recommendations.append("🔥 GPU utilization is excellent - maximum performance achieved")
            
            # Ollama-specific recommendations
            if ollama_status:
                if not ollama_status.is_gpu_accelerated:
                    recommendations.append("⚠️  Ollama is not using GPU acceleration - check configuration")
                else:
                    recommendations.append("✅ Ollama is successfully using GPU acceleration")
            
            # Model recommendations based on GPU memory
            available_memory = gpu_info.memory_total - gpu_info.memory_used
            if available_memory > 4000:  # 4GB available
                recommendations.append("🚀 Sufficient GPU memory available for larger models (7B+)")
            elif available_memory > 2000:  # 2GB available
                recommendations.append("📊 Moderate GPU memory available - suitable for 3B models")
            else:
                recommendations.append("💾 Limited GPU memory - consider smaller models or free memory")
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            recommendations.append("❌ Error analyzing GPU status")
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from recent metrics."""
        if not self.metrics_history:
            return {"status": "No metrics available"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        avg_gpu_util = sum(m.gpu_utilization for m in recent_metrics) / len(recent_metrics)
        avg_memory_usage = sum(m.gpu_memory_usage for m in recent_metrics) / len(recent_metrics)
        
        return {
            "current_timestamp": self.current_metrics.timestamp,
            "metrics_count": len(self.metrics_history),
            "average_gpu_utilization": round(avg_gpu_util, 2),
            "average_memory_usage": round(avg_memory_usage, 2),
            "current_ollama_memory": self.current_metrics.ollama_memory_usage,
            "total_requests": self.current_metrics.request_count,
            "total_tokens_processed": self.current_metrics.total_tokens_processed,
            "average_response_time": round(self.current_metrics.average_response_time, 3)
        }
    
    async def save_metrics_report(self, filepath: Path) -> None:
        """Save detailed metrics report to file."""
        try:
            gpu_info = await self.get_gpu_info()
            ollama_status = await self.get_ollama_gpu_status()
            recommendations = await self.get_optimization_recommendations()
            performance_summary = self.get_performance_summary()
            
            report = {
                "timestamp": time.time(),
                "gpu_info": gpu_info.__dict__ if gpu_info else None,
                "ollama_status": ollama_status.__dict__ if ollama_status else None,
                "performance_summary": performance_summary,
                "recommendations": recommendations,
                "recent_metrics": [
                    {
                        "timestamp": m.timestamp,
                        "gpu_utilization": m.gpu_utilization,
                        "gpu_memory_usage": m.gpu_memory_usage,
                        "ollama_memory_usage": m.ollama_memory_usage
                    }
                    for m in self.metrics_history[-100:]  # Last 100 metrics
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"GPU metrics report saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving metrics report: {e}")
    
    def record_inference_performance(self, tokens_generated: int, response_time: float) -> None:
        """Record performance metrics for an inference request."""
        self.current_metrics.request_count += 1
        self.current_metrics.total_tokens_processed += tokens_generated
        
        if response_time > 0:
            self.current_metrics.inference_speed = tokens_generated / response_time
        
        # Update rolling average response time
        total_requests = self.current_metrics.request_count
        current_avg = self.current_metrics.average_response_time
        self.current_metrics.average_response_time = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )


# Global GPU monitor instance
_gpu_monitor: Optional[GPUMonitor] = None


def get_gpu_monitor() -> GPUMonitor:
    """Get global GPU monitor instance."""
    global _gpu_monitor
    if _gpu_monitor is None:
        _gpu_monitor = GPUMonitor()
    return _gpu_monitor


async def check_gpu_health() -> Dict[str, Any]:
    """Quick GPU health check."""
    monitor = get_gpu_monitor()
    gpu_info = await monitor.get_gpu_info()
    ollama_status = await monitor.get_ollama_gpu_status()
    
    return {
        "gpu_available": gpu_info is not None,
        "gpu_name": gpu_info.name if gpu_info else None,
        "gpu_utilization": gpu_info.utilization if gpu_info else 0,
        "gpu_memory_usage": f"{gpu_info.memory_used}/{gpu_info.memory_total} MB" if gpu_info else "N/A",
        "gpu_temperature": gpu_info.temperature if gpu_info else None,
        "ollama_gpu_accelerated": ollama_status.is_gpu_accelerated if ollama_status else False,
        "ollama_model": ollama_status.model_name if ollama_status else None,
        "ollama_memory_usage": f"{ollama_status.gpu_memory_used} MB" if ollama_status else "N/A"
    }
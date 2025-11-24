"""
Observability Module for Bates Agent

Implements comprehensive logging, tracing, and metrics collection
for monitoring and analyzing agent performance and usage.
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import threading
from collections import defaultdict

class BatesLogger:
    """Enhanced logging system for the Bates Agent"""
    
    _loggers = {}
    _log_dir = Path("logs")
    
    @classmethod
    def setup_logging(cls):
        """Set up logging configuration"""
        cls._log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # File handler for all logs
        file_handler = logging.FileHandler(cls._log_dir / "bates_agent.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Error file handler
        error_handler = logging.FileHandler(cls._log_dir / "errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Add handlers if not already added
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(error_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger with the given name"""
        if name not in cls._loggers:
            cls.setup_logging()
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        return cls._loggers[name]

class BatesTracer:
    """Tracing system for tracking agent execution flows"""
    
    def __init__(self):
        self.traces = []
        self.current_trace = None
        self._lock = threading.Lock()
        
    def start_trace(self, operation: str, **kwargs) -> str:
        """Start a new trace"""
        trace_id = f"trace_{int(time.time() * 1000)}"
        
        with self._lock:
            trace_data = {
                "trace_id": trace_id,
                "operation": operation,
                "start_time": time.time(),
                "start_datetime": datetime.now().isoformat(),
                "metadata": kwargs,
                "events": [],
                "status": "started"
            }
            self.traces.append(trace_data)
            self.current_trace = trace_data
            
        return trace_id
    
    def add_event(self, event_type: str, message: str, **kwargs):
        """Add an event to the current trace"""
        if self.current_trace:
            with self._lock:
                event = {
                    "timestamp": time.time(),
                    "datetime": datetime.now().isoformat(),
                    "type": event_type,
                    "message": message,
                    "data": kwargs
                }
                self.current_trace["events"].append(event)
    
    def end_trace(self, status: str = "completed", **kwargs):
        """End the current trace"""
        if self.current_trace:
            with self._lock:
                self.current_trace["end_time"] = time.time()
                self.current_trace["end_datetime"] = datetime.now().isoformat()
                self.current_trace["duration"] = (
                    self.current_trace["end_time"] - self.current_trace["start_time"]
                )
                self.current_trace["status"] = status
                self.current_trace["result"] = kwargs
                self.current_trace = None
    
    def get_traces(self, limit: Optional[int] = None) -> list:
        """Get recent traces"""
        with self._lock:
            traces = sorted(self.traces, key=lambda x: x["start_time"], reverse=True)
            return traces[:limit] if limit else traces
    
    def export_traces(self, filepath: str):
        """Export traces to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_traces(), f, indent=2)

class BatesMetrics:
    """Metrics collection system for performance monitoring"""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = defaultdict(float)
        self._lock = threading.Lock()
        
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric"""
        with self._lock:
            self.counters[name] += value
    
    def record_timer(self, name: str, duration: float):
        """Record a timing metric"""
        with self._lock:
            self.timers[name].append({
                "duration": duration,
                "timestamp": time.time()
            })
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        with self._lock:
            self.gauges[name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        with self._lock:
            return {
                "counters": dict(self.counters),
                "timers": {
                    name: {
                        "count": len(times),
                        "total": sum(t["duration"] for t in times),
                        "avg": sum(t["duration"] for t in times) / len(times) if times else 0,
                        "recent": times[-10:]  # Last 10 measurements
                    }
                    for name, times in self.timers.items()
                },
                "gauges": dict(self.gauges),
                "timestamp": datetime.now().isoformat()
            }
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self.counters.clear()
            self.timers.clear()
            self.gauges.clear()

class PerformanceMonitor:
    """Context manager for monitoring function performance"""
    
    def __init__(self, operation_name: str, metrics: BatesMetrics, tracer: BatesTracer):
        self.operation_name = operation_name
        self.metrics = metrics
        self.tracer = tracer
        self.start_time = None
        self.trace_id = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.trace_id = self.tracer.start_trace(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metrics.record_timer(self.operation_name, duration)
        
        if exc_type:
            self.tracer.end_trace("error", error_type=str(exc_type), error_message=str(exc_val))
            self.metrics.increment_counter(f"{self.operation_name}_errors")
        else:
            self.tracer.end_trace("completed", duration=duration)
            self.metrics.increment_counter(f"{self.operation_name}_success")

# Global instances
_tracer = BatesTracer()
_metrics = BatesMetrics()

def get_tracer() -> BatesTracer:
    """Get the global tracer instance"""
    return _tracer

def get_metrics() -> BatesMetrics:
    """Get the global metrics instance"""
    return _metrics

def monitor_performance(operation_name: str):
    """Decorator for monitoring function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceMonitor(operation_name, _metrics, _tracer):
                return func(*args, **kwargs)
        return wrapper
    return decorator
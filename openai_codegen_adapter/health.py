"""
Health check and monitoring endpoints for the OpenAI Codegen Adapter.
Provides detailed health status, metrics, and diagnostic information.
"""

import logging
import psutil
import platform
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from .metrics import metrics_collector
from .error_handler import error_handler
from .config import get_codegen_config

logger = logging.getLogger(__name__)

# Create router for health endpoints
health_router = APIRouter(prefix="/health", tags=["health"])


def get_system_info() -> Dict[str, Any]:
    """Get system information for health checks."""
    try:
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
    except Exception as e:
        logger.warning(f"Could not get system info: {e}")
        return {"error": "System info unavailable"}


@health_router.get("/")
async def basic_health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "openai-codegen-adapter"
    }


@health_router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with metrics and system info."""
    try:
        # Get health status from metrics
        health_status = metrics_collector.get_health_status()
        
        # Get system information
        system_info = get_system_info()
        
        # Get error statistics
        error_stats = error_handler.get_error_stats()
        
        # Get recent metrics
        recent_stats = metrics_collector.get_summary_stats(time_window_minutes=5)
        
        return {
            "status": health_status["status"],
            "timestamp": datetime.now().isoformat(),
            "service": "openai-codegen-adapter",
            "uptime_minutes": health_status["uptime_minutes"],
            "health": health_status,
            "metrics": {
                "recent_5min": recent_stats,
                "endpoints": metrics_collector.get_endpoint_stats(),
                "models": metrics_collector.get_model_stats()
            },
            "errors": error_stats,
            "system": system_info
        }
    except Exception as e:
        logger.error(f"Error in detailed health check: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


@health_router.get("/metrics")
async def get_metrics():
    """Get detailed metrics for monitoring."""
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "last_hour": metrics_collector.get_summary_stats(time_window_minutes=60),
                "last_day": metrics_collector.get_summary_stats(time_window_minutes=1440),
                "all_time": metrics_collector.get_summary_stats()
            },
            "endpoints": metrics_collector.get_endpoint_stats(),
            "models": metrics_collector.get_model_stats(),
            "recent_requests": metrics_collector.get_recent_requests(limit=50)
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@health_router.get("/config")
async def get_config_status():
    """Get configuration status (without sensitive data)."""
    try:
        config = get_codegen_config()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "config_status": {
                "org_id_configured": bool(config.org_id),
                "token_configured": bool(config.token),
                "org_id_length": len(config.org_id) if config.org_id else 0,
                "token_prefix": config.token[:10] + "..." if config.token else None
            },
            "endpoints": {
                "openai_compatible": [
                    "/v1/chat/completions",
                    "/v1/completions",
                    "/v1/models"
                ],
                "anthropic_compatible": [
                    "/v1/messages",
                    "/v1/anthropic/completions"
                ],
                "gemini_compatible": [
                    "/v1/gemini/generateContent",
                    "/v1/gemini/completions"
                ],
                "health_endpoints": [
                    "/health",
                    "/health/detailed",
                    "/health/metrics",
                    "/health/config"
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error getting config status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@health_router.get("/readiness")
async def readiness_check():
    """Kubernetes-style readiness check."""
    try:
        # Check if we can get config
        config = get_codegen_config()
        
        # Check if required config is present
        if not config.org_id or not config.token:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "Missing required configuration (org_id or token)",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Check recent error rate
        recent_stats = metrics_collector.get_summary_stats(time_window_minutes=5)
        if recent_stats["total_requests"] > 0 and recent_stats["success_rate"] < 0.5:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": f"High error rate: {(1-recent_stats['success_rate'])*100:.1f}%",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in readiness check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@health_router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness check."""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }


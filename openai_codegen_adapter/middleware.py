"""
FastAPI middleware for request/response processing, logging, and metrics.
Provides centralized handling of CORS, request timing, and error logging.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .metrics import metrics_collector, RequestTimer
from .error_handler import error_handler

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses with timing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Log incoming request
        start_time = time.time()
        logger.info(f"🔄 [{request_id}] {request.method} {request.url.path} - Request started")
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"✅ [{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for error case
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"❌ [{request_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration_ms:.2f}ms"
            )
            
            # Handle error and return appropriate response
            return error_handler.handle_error(
                error=e,
                endpoint=request.url.path,
                request_id=request_id
            )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        with RequestTimer(metrics_collector, request.url.path, request.method) as timer:
            try:
                response = await call_next(request)
                timer.status_code = response.status_code
                return response
            except Exception as e:
                timer.status_code = 500
                raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def setup_middleware(app):
    """Set up all middleware for the FastAPI app."""
    
    # CORS middleware (should be first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Request logging middleware (should be last to capture all processing)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("🔧 Middleware setup completed")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware (for future use)."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.window_start = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host
        current_time = time.time()
        
        # Initialize tracking for new clients
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = 0
            self.window_start[client_ip] = current_time
        
        # Reset window if needed (1 minute window)
        if current_time - self.window_start[client_ip] >= 60:
            self.request_counts[client_ip] = 0
            self.window_start[client_ip] = current_time
        
        # Check rate limit
        if self.request_counts[client_ip] >= self.requests_per_minute:
            logger.warning(f"🚫 Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": "Rate limit exceeded",
                        "type": "rate_limit_error",
                        "code": "429"
                    }
                }
            )
        
        # Increment counter and process request
        self.request_counts[client_ip] += 1
        return await call_next(request)


#!/usr/bin/env python3
"""
Startup script for the Enterprise AI System backend.
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.is_development,
        log_config=None,  # Use our custom logging
        access_log=False  # Disable uvicorn access logs
    )


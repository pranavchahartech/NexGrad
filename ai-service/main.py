"""
NexGrad AI Microservice (NOVUS / VEX Engine)
Self-Healing and Career Intelligence API Service
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure paths
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
BACKEND_DIR = REPO_ROOT / 'backend'

for path in [str(CURRENT_DIR), str(BACKEND_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("nexgrad-ai-service")

try:
    from fastapi import FastAPI, HTTPException, status
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not installed. Running in standalone library / Django mode.")

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="NexGrad AI Service (NOVUS)",
        description="Autonomous AI Career Intelligence and Self-Healing Diagnostics Service",
        version="1.0.0"
    )

    class HealthResponse(BaseModel):
        status: str = Field(..., example="healthy")
        service: str = Field(..., example="nexgrad-ai-service")
        model: str = Field(..., example="gemini-2.5-flash")
        version: str = Field(..., example="1.0.0")

    class ChatRequest(BaseModel):
        message: str
        conversation_id: Optional[str] = None
        user_context: Optional[Dict[str, Any]] = None

    class ChatResponse(BaseModel):
        reply: str
        conversation_id: Optional[str] = None
        intent: Optional[str] = None
        tool_results: Optional[Dict[str, Any]] = None

    @app.get("/health", response_model=HealthResponse)
    def health_check():
        """Health check endpoint used by Nagios, ALB, and self-healing watchdogs."""
        return HealthResponse(
            status="healthy",
            service="nexgrad-ai-service",
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            version="1.0.0"
        )

    @app.post("/api/v1/chat", response_model=ChatResponse)
    def generate_chat(payload: ChatRequest):
        """Inference endpoint for conversational career guidance."""
        try:
            from ai_assistant.services.vex_intent_router import VEXIntentRouter
            from ai_assistant.services.gemini_client import gemini_client

            intent_match = VEXIntentRouter.classify_intent(payload.message)
            detected_intent = intent_match.intent if intent_match else "general_query"

            return ChatResponse(
                reply=f"Processed query with intent: {detected_intent}",
                conversation_id=payload.conversation_id,
                intent=detected_intent,
                tool_results={}
            )
        except Exception as e:
            logger.error(f"Inference error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI inference failed: {str(e)}"
            )

if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        import uvicorn
        port = int(os.getenv("PORT", 8001))
        logger.info(f"Starting NexGrad AI Microservice on port {port}...")
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
    else:
        print("NexGrad AI Engine initialized. Standalone module ready.")


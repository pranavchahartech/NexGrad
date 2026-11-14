# NexGrad AI Service (NOVUS / VEX Intelligence Engine)

Autonomous AI Career Intelligence, Natural-Language Intent Routing, and Infrastructure Diagnostic Service.

## Architecture

- **Engine**: Powered by Google Gemini (`gemini-2.5-flash`) via the Google GenAI SDK.
- **Intent Router**: `VEXIntentRouter` classifying 25+ natural language intents across career navigation, assessments, coding challenges, resume critique, and platform actions.
- **Context & Memory**: Deterministic conversation state management with tool persistence, profile retrieval, and memory synchronization.
- **Microservice Interface**: Standalone FastAPI runner with endpoints for health checks (`/health`), conversational inference (`/api/v1/chat`), and intent classification (`/api/v1/intent`).

## Directory Structure

```text
ai-service/
├── ai_assistant/        # Core Django modular AI application & services
│   ├── services/        # Gemini client, intent router, tools, memory, safety
│   ├── models.py        # AIMessage, ConversationState, StudentAIMemory
│   ├── views.py         # Chat endpoints and popup session handlers
│   └── tests.py         # 30 comprehensive unit & contextual intelligence tests
├── main.py              # Standalone FastAPI microservice runner
├── requirements.txt     # Dedicated AI service dependencies
├── Dockerfile           # Multi-stage production container image
└── README.md
```

## Running Standalone

```bash
pip install -r requirements.txt
python main.py
```

## Running Integrated with Django Backend

The Django backend seamlessly imports `ai-service/ai_assistant` directly via `sys.path`.
Execute tests from the repository root:

```bash
.\run test ai_assistant
```


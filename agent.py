"""
Runner script for the CMI Orchestrator Agent with session memory.
"""
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from .agent import root_agent

# Constants
APP_NAME = "CMI_Business_Solution"
USER_ID = "default_user"
SESSION_ID = "default_session"

# Initialize the session service (in-memory for development)
session_service = InMemorySessionService()

# Create the runner
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)


async def create_session():
    """Create a new session for the user."""
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    return session


async def run_agent(user_message: str):
    """
    Run the orchestrator agent with a user message.
    
    Args:
        user_message: The message from the user to process.
        
    Returns:
        The agent's response.
    """
    # Create content from user message
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    )
    
    # Run the agent and collect responses
    responses = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        responses.append(part.text)
    
    return "\n".join(responses)


async def interactive_chat():
    """Run an interactive chat session with the agent."""
    # Create initial session
    await create_session()
    
    print("=" * 60)
    print("CMI Business Solution - Orchestrator Agent")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the session.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            print("\nAgent: ", end="")
            response = await run_agent(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    asyncio.run(interactive_chat())




###server.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from agent import root_agent
import asyncio

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
APP_NAME = "CMI_Business_Solution"

# Initialize services
session_service = InMemorySessionService()

# Create runner
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Create session if it doesn't exist (or just ensure it's valid)
        # Note: create_session is idempotent in InMemorySessionService or we can just try/except
        # Ideally, we should check if session exists, but for now we can just ensure we can run with it.
        # InMemorySessionService.create_session typically stores it in a dict.
        try:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=request.user_id,
                session_id=request.session_id
            )
        except Exception:
            # Session likely already exists, which is fine
            pass

        content = types.Content(
            role="user",
            parts=[types.Part(text=request.message)]
        )

        response_text = ""
        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text

        return ChatResponse(response=response_text)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

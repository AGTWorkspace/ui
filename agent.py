import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from prompt import prompt
from sub_agents.Qualification_agent import Qualification_agent
from sub_agents.Pricing_agent import Pricing_agent
from sub_agents.Design_agent import Design_agent
from sub_agents.Communication_Agent import Communication_agent
from arize.otel import register
tracer_provider = register(
    space_id="U3BhY2U6MjI5NTA6T1A4dA==",      # Found in app space settings page
    api_key="ak-8ab8d973-95f2-48ae-b254-35f53faa766c-gnT5FvGep45UXNNSrkwGP2vvnpIN86Y3",        # Found in app space settings page
    project_name="CMI"  # Name this whatever you prefer
)
from openinference.instrumentation.google_adk import GoogleADKInstrumentor



GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
model = "gemini-3-pro-preview"

CMI_orchestrator_agent = LlmAgent(
    name="CMI_Orchestrator_Agent",
    model= model,
    description="you are a telecom agent to retrive the information of the customer.",
    instruction=prompt,
    # tools=[
    #     Qualification_agent,
    # #     # AgentTool(agent=Pricing_agent),
    # #     AgentTool(agent=Design_agent),
    # #     # AgentTool(agent=Communication_agent)
    # ],
    # sub_agents=[Design_agent,Pricing_agent,Communication_agent]
)
root_agent = CMI_orchestrator_agent


if __name__ == "__main__":
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

    async def run_chat():
        print("=" * 60)
        print("CMI Business Solution - Orchestrator Agent")
        print("=" * 60)
        print("Type 'quit' or 'exit' to end the session.\n")

        # Create session
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
        
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['quit', 'exit']:
                    break

                # Create content from user message
                content = types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                )

                print("\nAgent: ", end="")
                async for event in runner.run_async(
                    user_id=USER_ID,
                    session_id=SESSION_ID,
                    new_message=content
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if part.text:
                                    print(part.text)
                print()

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")

    asyncio.run(run_chat())

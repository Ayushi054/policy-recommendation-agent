import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

@pytest.mark.asyncio
async def test_agent_multi_turn_profile_collection() -> None:
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # Step 1: Start
    events = list(
        runner.run(
            new_message=types.Content(role="user", parts=[types.Part.from_text(text="Start")]),
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    # Check that we got RequestInput for ask_role
    assert any(e.content and any(p.function_call and p.function_call.name == "adk_request_input" and "ask_role" in str(p.function_call.args) for p in e.content.parts) for e in events)

    # Step 2: Provide role
    events = list(
        runner.run(
            new_message=types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name="adk_request_input",
                            response={"response": "Policymaker"},
                            id="ask_role"
                        )
                    )
                ]
            ),
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    # Check that we got RequestInput for ask_state
    assert any(e.content and any(p.function_call and p.function_call.name == "adk_request_input" and "ask_state" in str(p.function_call.args) for p in e.content.parts) for e in events)

    # Step 3: Provide state
    events = list(
        runner.run(
            new_message=types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name="adk_request_input",
                            response={"response": "Bihar"},
                            id="ask_state"
                        )
                    )
                ]
            ),
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    # Check that we got RequestInput for ask_domain
    assert any(e.content and any(p.function_call and p.function_call.name == "adk_request_input" and "ask_domain" in str(p.function_call.args) for p in e.content.parts) for e in events)

    # Step 4: Provide domain (sector)
    events = list(
        runner.run(
            new_message=types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name="adk_request_input",
                            response={"response": "healthcare"},
                            id="ask_domain"
                        )
                    )
                ]
            ),
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    # Check that we got RequestInput for ask_problem
    assert any(e.content and any(p.function_call and p.function_call.name == "adk_request_input" and "ask_problem" in str(p.function_call.args) for p in e.content.parts) for e in events)

    # Step 5: Provide problem
    events = list(
        runner.run(
            new_message=types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name="adk_request_input",
                            response={"response": "Lack of clean drinking water in primary healthcare centers."},
                            id="ask_problem"
                        )
                    )
                ]
            ),
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    
    # Let's inspect final session state
    updated_session = session_service.get_session_sync(
        session_id=session.id,
        app_name="test",
        user_id="test_user"
    )
    assert updated_session.state.get("user_domain") == "healthcare"

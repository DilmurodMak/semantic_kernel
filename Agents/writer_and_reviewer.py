"""
Multi-agent system with writer and reviewer agents using Semantic Kernel.

This module implements a collaborative writing system where a writer agent
creates content and a reviewer agent evaluates and provides feedback until
the content meets quality standards.
"""

import asyncio
import os
from typing import List

from semantic_kernel.agents import Agent, ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.agents import (
    GroupChatOrchestration,
    RoundRobinGroupChatManager
)
from semantic_kernel.agents.runtime import InProcessRuntime
from dotenv import load_dotenv


# Constants
WRITER_NAME = "Writer"
REVIEWER_NAME = "Reviewer"
MAX_ROUNDS = 5


def _get_environment_variables() -> tuple[str, str, str, str]:
    """Get required environment variables."""
    load_dotenv()
    
    # Use the exact same variable names as getting_started.py
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    
    if not all([api_key, deployment_name, endpoint, api_version]):
        raise ValueError(
            "Missing required environment variables. Please set "
            "AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME, "
            "AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_API_VERSION"
        )
    
    return api_key, deployment_name, endpoint, api_version


def _create_writer_instructions() -> str:
    """Create instructions for the writer agent."""
    return (
        "You are an excellent content writer. You create new content and "
        "edit contents based on the feedback. Always apply all review "
        "directions and revise the content in its entirety without "
        "explanation."
    )


def _create_reviewer_instructions() -> str:
    """Create instructions for the reviewer agent."""
    return (
        "You are an excellent content reviewer. You review the content and "
        "provide feedback to the writer. Evaluate based on clarity, accuracy, "
        "engagement, and language. Provide a score between 1-10 and specific "
        "suggestions for improvement if the score is 8 or below. If the score "
        "is above 8, state 'The article is good to go.'"
    )


def _get_agents() -> List[Agent]:
    """Create and return writer and reviewer agents."""
    (api_key, deployment_name,
     endpoint, api_version) = _get_environment_variables()
    
    # Create Azure Chat Completion service exactly like getting_started.py
    azure_chat_service = AzureChatCompletion(
        api_key=api_key,
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_version=api_version,
    )
    
    writer = ChatCompletionAgent(
        name=WRITER_NAME,
        description="A content writer.",
        instructions=_create_writer_instructions(),
        service=azure_chat_service,
    )
    
    reviewer = ChatCompletionAgent(
        name=REVIEWER_NAME,
        description="A content reviewer.",
        instructions=_create_reviewer_instructions(),
        service=azure_chat_service,
    )
    
    return [writer, reviewer]


def _agent_response_callback(message: ChatMessageContent) -> None:
    """Callback function to handle agent responses."""
    print(f"**{message.name}**")
    print(f"{message.content}")
    print()


async def _run_orchestration(task: str) -> str:
    """Run the group chat orchestration with the given task."""
    agents = _get_agents()

    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        manager=RoundRobinGroupChatManager(
            max_rounds=MAX_ROUNDS
        ),  # Odd number so writer gets the last word
        agent_response_callback=_agent_response_callback,
    )

    runtime = InProcessRuntime()
    runtime.start()

    try:
        orchestration_result = await group_chat_orchestration.invoke(
            task=task,
            runtime=runtime,
        )

        value = await orchestration_result.get()
        return value

    finally:
        await runtime.stop_when_idle()


async def _handle_user_interaction() -> None:
    """Handle the main user interaction loop."""
    print("Writer-Reviewer System Ready!")
    print("Type your content request, or 'exit' to quit.")

    while True:
        print()
        user_input = input("User > ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            break

        try:
            print("\n" + "=" * 50)
            print("STARTING COLLABORATION")
            print("=" * 50)

            result = await _run_orchestration(user_input)

            print("=" * 50)
            print("FINAL RESULT")
            print("=" * 50)
            print(result)

        except Exception as e:
            print(f"Error during collaboration: {e}")


async def main() -> None:
    """Main function to run the writer-reviewer agent system."""
    try:
        await _handle_user_interaction()
    except Exception as e:
        print(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.agents import ChatHistoryAgentThread
import os
import asyncio
from dotenv import load_dotenv

kernel = Kernel()

load_dotenv()
# Load environment variables from .env file
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")


async def main():
    # Initialize the kernel
    kernel = Kernel()

    # Add Azure OpenAI chat completion
    kernel.add_service(
        AzureChatCompletion(
            api_key=api_key,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_version=api_version,
        )
    )

    arguments = KernelArguments(
        settings=PromptExecutionSettings(
            # Set the function_choice_behavior to auto to let the model
            # decide which function to use, and let the kernel automatically
            # execute the functions.
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )
    )

    # Create the agent using the kernel
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="ChatCompletionAgent",
        instructions="You are a helpful AI assistant",
        arguments=arguments,
    )

    response = await agent.get_response(messages="Hello how are you?")
    print(response)

    # Define the thread
    thread = ChatHistoryAgentThread()

    continueChat = True

    while continueChat:
        user_input = input("Enter your query: ")
        if user_input.lower() == "exit":
            continueChat = False
            break
        response = await agent.get_response(messages=user_input, thread=thread)
        print(response)


if __name__ == "__main__":
    asyncio.run(main())

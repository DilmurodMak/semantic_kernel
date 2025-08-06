from semantic_kernel import Kernel
import os
import asyncio
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from dotenv import load_dotenv
from typing import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory

load_dotenv()

azure_ai_foundry_endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT_PORTAL")
azure_openai_key = os.getenv("AZURE_AI_FOUNDRY_OPENAI_KEY")
azure_openai_deployment_name = os.getenv("AZURE_AI_FOUNDRY_OPENAI_DEPLOYMENT")
azure_openai_endpoint = os.getenv("AZURE_AI_FOUNDRY_OPENAI_ENDPOINT")
azure_openai_api_version = os.getenv("AZURE_AI_FOUNDRY_OPENAI_API_VERSION")
bing_connection_name = os.getenv("BING_CONNECTION_NAME")


class Agents:
    def __init__(self, project_client: AIProjectClient):
        self.project_client = project_client

    @kernel_function(
        description="This function will be used to use an azure ai agent with web grounding capability using Bing Search API",
        name="WebSearchAgent",
    )
    def web_search_agent(
        self,
        query: Annotated[
            str,
            "The user query for which the contextual information needs to be fetched from the web",
        ],
    ) -> Annotated[str, "The response from the web search agent"]:
        bing_connection = self.project_client.connections.get(name=bing_connection_name)
        conn_id = bing_connection.id
        bing = BingGroundingTool(connection_id=conn_id)

        agent = self.project_client.agents.create_agent(
            model=azure_openai_deployment_name,
            name="bing-assistant",
            instructions="You are a helpful assistant",
            tools=bing.definitions,
        )
        thread = self.project_client.agents.threads.create()

        message = self.project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=query,
        )

        run = self.project_client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id,
        )
        print(f"Run completed with status: {run.status}")

        messages = self.project_client.agents.messages.list(thread_id=thread.id)

        for message in messages:
            print(f"Role: {message.role}, Content: {message.content}")

        # Return the assistant's response (last message with role='assistant')
        assistant_messages = [m for m in messages if m.role == "assistant"]
        return assistant_messages[0].content if assistant_messages else ""

    @kernel_function(
        description="This function will use an azure ai agent to prepare a script for a news reporter based on latest information for a specific topic",
        name="NewsReporterAgent",
    )
    def news_reporter_agent(
        self,
        topic: Annotated[
            str, "The topic for which the latest information/news has been fetched"
        ],
        latest_news: Annotated[str, "The latest information for a specific topic"],
    ) -> Annotated[
        str,
        "the response from the NewsReporterAgent which is the script for a news reporter",
    ]:

        agent = self.project_client.agents.create_agent(
            model=azure_openai_deployment_name,
            name="news-reporter",
            instructions="""You are a helpful assistant that is meant to prepare a script for a news reporter based on the latest information for a specific topic both of which you will be given.
            The news channel is named MSinghTV and the news reporter is named John. You will be given the topic and the latest information for that topic. Prepare a script for the news reporter John based on the latest information for the topic.""",
        )
        thread = self.project_client.agents.threads.create()

        message = self.project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"""The topic is {topic} and the latest information is {latest_news}""",
        )

        run = self.project_client.agents.runs.create_and_process(
            thread_id=thread.id, agent_id=agent.id
        )
        print(f"Run completed with status: {run.status}")

        messages = self.project_client.agents.messages.list(thread_id=thread.id)

        print("Script for the news reporter:")
        print("\n")
        for message in messages:
            print(f"Role: {message.role}, Content: {message.content}")

        # Return the assistant's response (last message with role='assistant')
        assistant_messages = [m for m in messages if m.role == "assistant"]
        return assistant_messages[0].content if assistant_messages else ""


async def main():
    # Initialize the project client globally
    project_client = AIProjectClient(
        endpoint=azure_ai_foundry_endpoint, credential=DefaultAzureCredential()
    )

    # Test Bing connection (optional verification step)
    try:
        bing_connection = project_client.connections.get(name=bing_connection_name)
        print(f"✅ Bing connection verified, ID: {bing_connection.id}")
    except Exception as e:
        print(f"❌ Error verifying Bing connection: {e}")
        return

    # Initialize Semantic Kernel
    kernel = Kernel()

    chat_completion = AzureChatCompletion(
        api_key=azure_openai_key,
        deployment_name=azure_openai_deployment_name,
        endpoint=azure_openai_endpoint,
        api_version=azure_openai_api_version,
    )

    kernel.add_service(chat_completion)

    # Add the Agents plugin with project_client
    kernel.add_plugin(Agents(project_client), "Agents")

    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create a history of the conversation
    history = ChatHistory()

    userInput = None
    while True:
        # Collect user input
        userInput = input("User > ")

        # Terminate the loop if the user says "exit"
        if userInput == "exit":
            break

        # Add user input to the history
        history.add_user_message(userInput)

        # 3. Get the response from the AI with automatic function calling
        result = await chat_completion.get_chat_message_content(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel,
        )

        # Print the results
        print("Assistant > " + str(result))

        # Add the message from the agent to the chat history
        history.add_message(result)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())

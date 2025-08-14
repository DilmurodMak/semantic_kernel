import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
# Commenting out Semantic Kernel imports due to version compatibility issue
# from semantic_kernel.agents import AzureAIAgentThread, AzureAIAgent
from azure.ai.agents.models import (
    OpenApiTool,
    OpenApiAnonymousAuthDetails,
    CodeInterpreterTool,
    ToolSet
)
from dotenv import load_dotenv
from pathlib import Path
import jsonref

load_dotenv()

model = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")

project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)

with open(
    os.path.join(os.path.dirname(__file__), "weather_openapi.json"), "r"
) as f:
    openapi_spec = jsonref.loads(f.read())

# Create Auth object for the OpenApiTool
auth = OpenApiAnonymousAuthDetails()

# Create the OpenAPI tool using the correct class name
openapi_tool = OpenApiTool(
    name="get_weather",
    spec=openapi_spec,
    description="Retrieve weather information for a location",
    auth=auth,
)

# Create code interpreter tool for chart generation
code_interpreter = CodeInterpreterTool()

# Create toolset and add both tools (using the correct pattern)
toolset = ToolSet()
toolset.add(openapi_tool)
toolset.add(code_interpreter)


def main():
    """Main function to create and configure the Azure AI Agent."""
    try:
        # Create agent using the Azure AI Projects API directly
        agent = project_client.agents.create_agent(
            model=model,
            name="multiple-tools-assistant",
            instructions=(
                "You are a helpful assistant that can retrieve weather "
                "information for any location and generate charts."
            ),
            tools=toolset.definitions,  # Use toolset.definitions
            tool_resources=toolset.resources,  # Use toolset.resources
        )

        print(f"Agent created successfully with ID: {agent.id}")
        agent_id = agent.id

        # Create thread
        thread = project_client.agents.threads.create()
        print(f"Created thread, thread ID: {thread.id}")
        thread_id = thread.id

        # User input requesting weather and chart
        user_input = (
            "What is the weather in Tashkent for today and generate a chart ?"
        )

        # Create user message
        message = project_client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input,
        )
        print(f"Created message, ID: {message.id}")

        # Create and process the run
        run = project_client.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=agent_id
        )
        print(f"Run finished with status: {run.status}")

        if run.status == "failed":
            print(f"Run failed: {run.last_error}")

        # Get final messages
        messages = project_client.agents.messages.list(thread_id=thread_id)
        
        # Check for image content in messages
        print("\nChecking for image content:")
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                for content_item in msg.content:
                    if (hasattr(content_item, 'type') and
                            content_item.type == 'image_file'):
                        file_id = content_item.image_file.file_id
                        print(f"Image content found: {file_id}")

        # Save the iamge file if found    
        file_name = f"{file_id}_image_file.png"
        print(f"Would save image file to: {Path.cwd() / file_name}")
        project_client.agents.files.save(file_id=file_id, file_name=file_name)
    
        print("\nFinal conversation:")
        for msg in messages:
            print(f"{msg.role}: {msg.content}")

        # Cleanup
        project_client.agents.delete_agent(agent_id)
        print("Deleted agent")

        return agent

    except Exception as e:
        print(f"Error creating agent: {str(e)}")


if __name__ == "__main__":
    main()

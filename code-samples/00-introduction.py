from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
import os
import asyncio
from dotenv import load_dotenv

kernel = Kernel()

load_dotenv()

service_id = "default"
kernel.add_service(
    AzureChatCompletion(
        service_id=service_id,
        api_key=os.getenv("AZURE_AI_FOUNDRY_API_KEY"),
        deployment_name=os.getenv("AZURE_AI_FOUNDRY_DEPLOYMENT"),
        endpoint=os.getenv("AZURE_AI_FOUNDRY_ENDPOINT"),
        api_version=os.getenv("AZURE_AI_FOUNDRY_API_VERSION"),
    )
)

plugin_path = os.path.join(
    os.path.dirname(__file__), "..", "plugins", "prompt_templates"
)
plugin = kernel.add_plugin(
    parent_directory=plugin_path,
    plugin_name="basic_plugin"
)

greeting_function = plugin["greeting"]


async def greeting():
    return await kernel.invoke(
        greeting_function,
        KernelArguments(name="Dilmurod", age="35")
    )


greeting_response = asyncio.run(greeting())

print(greeting_response)

from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor

OpenAIInstrumentor().instrument()

project_client = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://semantic-aifoundry.services.ai.azure.com/api/projects/firstProject",
)

connection_string = project_client.telemetry.get_application_insights_connection_string()


configure_azure_monitor(connection_string=connection_string)

client = project_client.get_openai_client()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Write a short poem on open telemetry."},
    ],
)


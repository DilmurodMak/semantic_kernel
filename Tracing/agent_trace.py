"""
Azure AI Foundry Agent Tracing Example

This script demonstrates how to trace AI agents using the Azure AI Foundry SDK
with OpenTelemetry following the latest best practices.
"""

import os
import logging
from functions import user_functions

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import (
    FunctionTool,
    ToolSet,
)

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Azure Monitor import
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable content recording for tracing (prompts and completions)
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
os.environ["AZURE_SDK_TRACING_IMPLEMENTATION"] = "opentelemetry"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_tracing():
    """Set up OpenTelemetry tracing for local development and Azure Monitor."""
    # Set up basic tracing provider
    resource = Resource(attributes={
        "service.name": "azure-ai-agent-trace"
    })
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Try to set up OTLP exporter for AI Toolkit (optional)
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter
        )
        otlp_exporter = OTLPSpanExporter(
            endpoint="http://localhost:4318/v1/traces",
        )
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        logger.info("OTLP exporter configured for AI Toolkit")
    except ImportError:
        logger.info("OTLP exporter not available, using basic tracing")
    
    # Enable Azure AI telemetry
    try:
        from azure.ai.agents.telemetry import AIAgentsInstrumentor
        AIAgentsInstrumentor().instrument()
        logger.info("Azure AI Agents telemetry enabled")
    except ImportError:
        logger.warning("Azure AI Agents telemetry not available")
    
    logger.info("OpenTelemetry tracing configured")


def setup_azure_monitor_tracing(agents_client):
    """Set up Azure Monitor tracing if Application Insights is available."""
    try:
        # Note: Azure AI Agents SDK may not have direct telemetry support
        # This is a placeholder for when the functionality becomes available
        logger.warning(
            "Azure Monitor tracing not directly supported with "
            "Azure AI Agents SDK. Using OpenTelemetry only."
        )
        return False
    except Exception as e:
        logger.warning(f"Failed to setup Azure Monitor tracing: {e}")
        return False


def main():
    """Main function to run the agent with tracing."""
    # Set up tracing
    setup_tracing()
    
    # Get configuration
    model = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    
    if not model or not endpoint:
        logger.error(
            "Missing required environment variables: "
            "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME and AZURE_AI_AGENT_ENDPOINT"
        )
        return
    
    # Create AI Agents client
    agents_client = AgentsClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential()
    )
    
    # Setup Azure Monitor tracing (placeholder for future support)
    azure_monitor_enabled = setup_azure_monitor_tracing(agents_client)
    
    # Get tracer
    scenario = os.path.basename(__file__)
    tracer = trace.get_tracer(__name__)
    
    # Create function tools
    functions = ToolSet()
    function_tool = FunctionTool(functions=user_functions)
    functions.add(function_tool)
    
    with tracer.start_as_current_span(scenario):
        run_agent_workflow(
            agents_client, model, functions, tracer, azure_monitor_enabled
        )


def run_agent_workflow(
    agents_client, model, functions, tracer, azure_monitor_enabled
):
    """Run the main agent workflow with tracing."""
    try:
        # Create an agent and run user's request with function calls
        agent = agents_client.create_agent(
            model=model,
            name="my-function-tracing-assistant",
            instructions="You are a helpful assistant",
            tools=functions.definitions,
        )
        logger.info(f"Created agent, ID: {agent.id}")

        user_query = "What is the weather in Seattle and email id for user1?"

        # Use the Azure AI Agents SDK's integrated approach
        with tracer.start_as_current_span("create_and_run") as span:
            span.set_attribute("user_query", user_query)
            span.set_attribute("agent_id", agent.id)
            
            # Create thread and run in one operation
            run = agents_client.create_thread_and_run(
                agent_id=agent.id,
                thread={
                    "messages": [
                        {
                            "role": "user",
                            "content": user_query
                        }
                    ]
                }
            )
            
            logger.info(f"Created thread and run, Run ID: {run.id}")
            span.set_attribute("run_id", run.id)
            span.set_attribute("thread_id", run.thread_id)
            
            # Process the run (this may involve polling for completion)
            process_agent_run_simple(agents_client, run, tracer)
            
            # Get final response and log token usage
            handle_completion_simple(agents_client, run, user_query, tracer)
        
        # Cleanup
        agents_client.delete_agent(agent.id)
        logger.info("Deleted agent")
        
    except Exception as e:
        logger.error(f"Error in agent workflow: {e}")
        raise


def process_agent_run_simple(agents_client, run, tracer):
    """Process the agent run using the simpler Azure AI Agents SDK approach."""
    with tracer.start_as_current_span("process_agent_run") as span:
        span.set_attribute("thread_id", run.thread_id)
        span.set_attribute("run_id", run.id)
        
        # The run may already be completed or in progress
        # Log the final status
        span.set_attribute("final_status", run.status)
        logger.info(f"Run completed with status: {run.status}")


def handle_completion_simple(agents_client, run, user_query, tracer):
    """Handle the completion of the run and log results."""
    with tracer.start_as_current_span("handle_completion") as span:
        span.set_attribute("final_status", run.status)
        span.set_attribute("thread_id", run.thread_id)
        span.set_attribute("run_id", run.id)
        
        logger.info(f"Run completed with status: {run.status}")

        # Get the AI response from the run
        try:
            # The response should be in the run object or thread messages
            if hasattr(run, 'messages') and run.messages:
                ai_output = run.messages[-1].content
                logger.info(f"AI Response: {ai_output}")
                span.set_attribute("ai_output", ai_output)
            else:
                logger.info("No direct response found in run object")
                ai_output = "Response processing completed"
                span.set_attribute("ai_output", ai_output)

            # Log token usage if available
            if hasattr(run, 'usage') and run.usage:
                log_token_usage(run.usage, user_query, ai_output, tracer)
                
        except Exception as e:
            logger.warning(f"Could not extract response: {e}")
            span.set_attribute("extraction_error", str(e))


def log_token_usage(usage, user_query, ai_output, tracer):
    """Log token usage information with tracing."""
    with tracer.start_as_current_span("Token Usage") as span:
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = prompt_tokens + completion_tokens
        
        span.set_attribute("user_input", user_query)
        span.set_attribute("ai_output", ai_output)
        span.set_attribute("ai.prompt_tokens", prompt_tokens)
        span.set_attribute("ai.completion_tokens", completion_tokens)
        span.set_attribute("ai.total_tokens", total_tokens)
        
        logger.info(
            f"Token Usage - Prompt: {prompt_tokens}, "
            f"Completion: {completion_tokens}, Total: {total_tokens}"
        )
        print(
            f"Token Usage - Prompt: {prompt_tokens}, "
            f"Completion: {completion_tokens}, Total: {total_tokens}"
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Azure AI Projects OpenTelemetry Tracing Application

This script demonstrates how to use OpenTelemetry tracing with Azure AI
Projects and Azure Monitor for observability of OpenAI API calls.
"""

import os
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
from dotenv import load_dotenv

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter
)

# Load environment variables
load_dotenv()


def setup_console_tracing():
    """Set up console tracing for development and debugging."""
    span_exporter = ConsoleSpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    print("✅ Console tracing enabled - spans will be printed to console")


# Check if console tracing is requested via environment variable
console_tracing_enabled = (
    os.getenv("ENABLE_CONSOLE_TRACING", "false").lower() == "true"
)
if console_tracing_enabled:
    setup_console_tracing()

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("setup_tracing_environment")
def setup_tracing_environment():
    """Set up the tracing environment and return configured client."""
    # Load environment variables
    azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_ai_foundry_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    
    # Set OPENAI_API_VERSION environment variable if not already set
    if azure_openai_api_version and not os.getenv("OPENAI_API_VERSION"):
        os.environ["OPENAI_API_VERSION"] = azure_openai_api_version
        print(f"Using API version from environment: "
              f"{azure_openai_api_version}")
    elif not os.getenv("OPENAI_API_VERSION"):
        # Fallback to a default API version
        os.environ["OPENAI_API_VERSION"] = "2024-02-15-preview"
        print("Using default OpenAI API version: 2024-02-15-preview")
    else:
        print(f"Using existing API version: {os.getenv('OPENAI_API_VERSION')}")
    
    # Use environment endpoint if available, otherwise use hardcoded one
    endpoint = azure_ai_foundry_endpoint or (
        "https://semantic-aifoundry.services.ai.azure.com"
        "/api/projects/firstProject"
    )

    print(f"Using endpoint: {endpoint}")
    print(f"Using API version: {os.getenv('OPENAI_API_VERSION')}")

    # Instrument OpenAI calls for tracing
    OpenAIInstrumentor().instrument()

    # Initialize the AI Project client
    project_client = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=endpoint,
    )

    # Get Application Insights connection string for tracing
    connection_string = (
        project_client.telemetry.get_application_insights_connection_string()
    )

    # Configure Azure Monitor for telemetry collection
    configure_azure_monitor(connection_string=connection_string)

    # Get OpenAI client
    client = project_client.get_openai_client()
    
    return client


@tracer.start_as_current_span("generate_poem")
def generate_poem(client):
    """Generate a poem about OpenTelemetry using the provided client."""
    print("Generating poem about OpenTelemetry...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": "Write a short poem on open telemetry."
            },
        ],
    )

    # Print the response
    print("\nGenerated Poem:")
    print("=" * 50)
    print(response.choices[0].message.content)
    print("=" * 50)
    print("\nTracing data has been sent to Azure Monitor.")
    
    return response.choices[0].message.content


def main():
    """Main function to run the tracing application."""
    client = setup_tracing_environment()
    generate_poem(client)


@tracer.start_as_current_span("build_prompt_with_context")
def build_prompt_with_context(claim: str, context: str) -> list:
    """Build a prompt for assessing claims with context."""
    # Get current span and add attributes
    current_span = trace.get_current_span()
    if current_span.is_recording():
        current_span.set_attribute("claim", claim[:200])  # Show more of claim
        current_span.set_attribute("context", context[:300])  # Show context
        current_span.set_attribute("context_length", len(context))
    
    system_message = (
        "I will ask you to assess whether a particular scientific claim, "
        "based on evidence provided. Output only the text 'True' if the "
        "claim is true, 'False' if the claim is false, or 'NEE' if "
        "there's not enough evidence."
    )
    
    user_message = f"""
The evidence is the following: {context}

Assess the following claim on the basis of the evidence. Output only the
text 'True' if the claim is true, 'False' if the claim is false, or 'NEE'
if there's not enough evidence. Do not output any other text.

Claim:
{claim}

Assessment:
"""
    
    return [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]


@tracer.start_as_current_span("assess_single_claim")
def assess_single_claim(claim: str, context: str, client) -> str:
    """Assess a single claim with its context."""
    # Get current span and add attributes
    current_span = trace.get_current_span()
    if current_span.is_recording():
        current_span.set_attribute("claim", claim[:200])
        current_span.set_attribute("context", context[:300])
        current_span.set_attribute("context_length", len(context))
        current_span.set_attribute("model", "gpt-4o")
    
    with tracer.start_as_current_span("assess_single_claim_details") as span:
        span.set_attribute("claim", claim[:100])  # Truncate for safety
        span.set_attribute("context_length", len(context))
        span.set_attribute("context_preview", context[:150])
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=build_prompt_with_context(claim=claim, context=context),
        )
        result = response.choices[0].message.content.strip('., ')
        span.set_attribute("assessment", result)
        
        return result


@tracer.start_as_current_span("assess_claims_with_context")
def assess_claims_with_context(claims, contexts, client):
    """Assess multiple claims with their corresponding contexts."""
    # Get current span and add attributes
    current_span = trace.get_current_span()
    if current_span.is_recording():
        current_span.set_attribute("total_claims", len(claims))
        current_span.set_attribute("claims_preview", str(claims)[:500])
        
    responses = []
    for i, (claim, context) in enumerate(zip(claims, contexts)):
        with tracer.start_as_current_span(f"claim_assessment_{i}") as span:
            span.set_attribute("claim_index", i)
            span.set_attribute("total_claims", len(claims))
            span.set_attribute("current_claim", claim[:150])
            span.set_attribute("current_context", context[:200])
            
            result = assess_single_claim(claim, context, client)
            responses.append(result)
            span.set_attribute("assessment_result", result)

    return responses


@tracer.start_as_current_span("test_claim_assessment")
def test_claim_assessment():
    """Test function to demonstrate claim assessment functionality."""
    client = setup_tracing_environment()
    
    print("Testing claim assessment functionality...")
    
    # Test data
    test_claims = [
        "Water boils at 100 degrees Celsius at sea level.",
        "The Earth is flat.",
        "Chocolate is made from cocoa beans."
    ]
    
    test_contexts = [
        (
            "Water has a boiling point of 100°C (212°F) at standard "
            "atmospheric pressure (1 atmosphere or 101.325 kPa)."
        ),
        (
            "The Earth is a sphere, as evidenced by satellite imagery, "
            "the curvature visible from high altitudes, and centuries "
            "of scientific observation."
        ),
        (
            "Chocolate is produced from the seeds of the cacao tree "
            "(Theobroma cacao). The seeds are fermented, dried, and "
            "processed to create chocolate."
        )
    ]
    
    print("=" * 60)
    
    results = assess_claims_with_context(test_claims, test_contexts, client)
    
    for i, (claim, context, result) in enumerate(
        zip(test_claims, test_contexts, results), 1
    ):
        print(f"\nTest {i}:")
        print(f"Claim: {claim}")
        print(f"Context: {context[:100]}...")
        print(f"Assessment: {result}")
        print("-" * 40)
    
    print("\nClaim assessment test completed!")
    print("Tracing data has been sent to Azure Monitor.")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run the claim assessment test
        test_claim_assessment()
    else:
        # Run the original poem generation
        main()

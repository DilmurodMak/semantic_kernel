#!/usr/bin/env python3
"""
OpenTelemetry Tracing Utilities

Reusable tracing components for OpenTelemetry with Azure Monitor integration
and console output support.
"""

import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter
)
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


class TracingManager:
    """Manages OpenTelemetry tracing setup and configuration."""
    
    def __init__(self, service_name: str = "semantic_kernel_app"):
        """
        Initialize the tracing manager.
        
        Args:
            service_name: Name of the service for tracing identification
        """
        self.service_name = service_name
        self.tracer = None
        self.console_tracing_enabled = False
        self.azure_monitor_enabled = False
        
        # Load environment variables
        load_dotenv()
        
    def setup_console_tracing(self) -> None:
        """Set up console tracing for development and debugging."""
        span_exporter = ConsoleSpanExporter()
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
        trace.set_tracer_provider(tracer_provider)
        self.console_tracing_enabled = True
        print("✅ Console tracing enabled - spans will be printed to console")
    
    def setup_azure_monitor_tracing(self, project_client: AIProjectClient) -> None:
        """
        Set up Azure Monitor tracing.
        
        Args:
            project_client: Azure AI Project client for getting connection string
        """
        try:
            connection_string = (
                project_client.telemetry.get_application_insights_connection_string()
            )
            configure_azure_monitor(connection_string=connection_string)
            self.azure_monitor_enabled = True
            print("✅ Azure Monitor tracing configured")
        except Exception as e:
            print(f"⚠️ Warning: Could not configure Azure Monitor: {e}")
    
    def setup_openai_instrumentation(self) -> None:
        """Set up OpenAI instrumentation for automatic tracing."""
        OpenAIInstrumentor().instrument()
        print("✅ OpenAI instrumentation enabled")
    
    def initialize_tracer(self) -> trace.Tracer:
        """
        Initialize and return a tracer instance.
        
        Returns:
            Configured OpenTelemetry tracer
        """
        # Check if console tracing is requested via environment variable
        console_tracing_requested = (
            os.getenv("ENABLE_CONSOLE_TRACING", "false").lower() == "true"
        )
        
        if console_tracing_requested and not self.console_tracing_enabled:
            self.setup_console_tracing()
        
        self.tracer = trace.get_tracer(self.service_name)
        return self.tracer
    
    def get_tracer(self) -> trace.Tracer:
        """
        Get the current tracer instance.
        
        Returns:
            Current tracer or creates new one if not initialized
        """
        if self.tracer is None:
            return self.initialize_tracer()
        return self.tracer


class TracingHelper:
    """Helper functions for adding attributes to spans."""
    
    @staticmethod
    def add_claim_attributes(span: trace.Span, claim: str, 
                           context: str = None, limit: int = 200) -> None:
        """
        Add claim and context attributes to a span.
        
        Args:
            span: OpenTelemetry span to add attributes to
            claim: The claim text
            context: Optional context text
            limit: Character limit for truncation
        """
        if span.is_recording():
            span.set_attribute("claim", claim[:limit])
            if context:
                span.set_attribute("context", context[:min(limit + 100, 300)])
                span.set_attribute("context_length", len(context))
    
    @staticmethod
    def add_context_attributes(span: trace.Span, context: str, 
                             limit: int = 300) -> None:
        """
        Add context attributes to a span.
        
        Args:
            span: OpenTelemetry span to add attributes to
            context: The context text
            limit: Character limit for truncation
        """
        if span.is_recording():
            span.set_attribute("context", context[:limit])
            span.set_attribute("context_length", len(context))
    
    @staticmethod
    def add_assessment_attributes(span: trace.Span, assessment: str) -> None:
        """
        Add assessment result attributes to a span.
        
        Args:
            span: OpenTelemetry span to add attributes to
            assessment: The assessment result
        """
        if span.is_recording():
            span.set_attribute("assessment", assessment)
            span.set_attribute("assessment_length", len(assessment))
    
    @staticmethod
    def add_assessment_full_attributes(span: trace.Span, claim: str, context: str,
                                     assessment: str, model: str = "gpt-4o") -> None:
        """
        Add assessment-specific attributes to a span.
        
        Args:
            span: OpenTelemetry span to add attributes to
            claim: The claim being assessed
            context: The context for assessment
            assessment: The assessment result
            model: The model used for assessment
        """
        if span.is_recording():
            span.set_attribute("claim", claim[:150])
            span.set_attribute("context_preview", context[:200])
            span.set_attribute("context_length", len(context))
            span.set_attribute("assessment", assessment)
            span.set_attribute("model", model)
    
    @staticmethod
    def add_batch_attributes(span: trace.Span, claims: list, contexts: list) -> None:
        """
        Add batch processing attributes for claims and contexts to a span.
        
        Args:
            span: OpenTelemetry span to add attributes to
            claims: List of claims being processed
            contexts: List of contexts for the claims
        """
        if span.is_recording():
            span.set_attribute("total_claims", len(claims))
            span.set_attribute("total_contexts", len(contexts))
            span.set_attribute("claims_preview", str(claims)[:300])
            span.set_attribute("contexts_preview", str(contexts)[:300])
    
    @staticmethod
    def add_batch_items_attributes(span: trace.Span, items: list, 
                                 item_type: str = "items") -> None:
        """
        Add batch processing attributes to a span.
        
        Args:
            span: OpenTelemetry span to add attributes to
            items: List of items being processed
            item_type: Type description for the items
        """
        if span.is_recording():
            span.set_attribute(f"total_{item_type}", len(items))
            span.set_attribute(f"{item_type}_preview", str(items)[:500])


def create_tracer(service_name: str = "semantic_kernel_app") -> trace.Tracer:
    """
    Convenience function to create a tracer with default settings.
    
    Args:
        service_name: Name of the service for tracing
        
    Returns:
        Configured OpenTelemetry tracer
    """
    manager = TracingManager(service_name)
    return manager.initialize_tracer()


def setup_environment_variables() -> dict:
    """
    Set up OpenTelemetry environment variables from Azure configuration.
    
    Returns:
        Dictionary with environment configuration
    """
    load_dotenv()
    
    azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_ai_foundry_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    
    # Set OPENAI_API_VERSION environment variable if not already set
    if azure_openai_api_version and not os.getenv("OPENAI_API_VERSION"):
        os.environ["OPENAI_API_VERSION"] = azure_openai_api_version
        print(f"Using API version from environment: {azure_openai_api_version}")
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
    
    return {
        "api_version": os.getenv("OPENAI_API_VERSION"),
        "endpoint": endpoint,
        "azure_api_version": azure_openai_api_version,
        "azure_endpoint": azure_ai_foundry_endpoint
    }


def create_azure_client(endpoint: str) -> AIProjectClient:
    """
    Create Azure AI Project client.
    
    Args:
        endpoint: Azure AI Foundry endpoint
        
    Returns:
        Configured Azure AI Project client
    """
    return AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=endpoint,
    )

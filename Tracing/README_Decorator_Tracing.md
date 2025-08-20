# OpenTelemetry Decorator-Based Tracing Implementation

This document explains the decorator-based tracing approach implemented in the `tracing_application.py` file.

## Overview

The application now uses a custom decorator `@trace_function` to automatically add OpenTelemetry tracing to functions, making the code cleaner and more maintainable.

## Key Features

### 1. Custom Tracing Decorator

```python
@trace_function(operation_name="custom_name", include_args=True, include_result=True)
def my_function(arg1, arg2):
    # Function implementation
    return result
```

The decorator provides:
- **Automatic span creation** with configurable names
- **Argument tracking** (can be disabled for sensitive data)
- **Result tracking** (can be disabled for large results)
- **Exception handling** with automatic error recording
- **Performance metrics** (duration, status)

### 2. Decorator Parameters

- `operation_name`: Custom span name (defaults to `module.function_name`)
- `include_args`: Whether to include function arguments as span attributes
- `include_result`: Whether to include function result as span attributes

### 3. Traced Functions

#### Setup Functions
- `@trace_function("setup_tracing_environment")` - Environment and client setup
- `@trace_function("generate_poem", include_args=True, include_result=False)` - Poem generation

#### Claim Assessment Functions
- `@trace_function("build_prompt_with_context", include_result=False)` - Prompt building
- `@trace_function("assess_single_claim", include_args=False, include_result=True)` - Single claim assessment
- `@trace_function("assess_claims_with_context", include_args=False)` - Multiple claims assessment
- `@trace_function("test_claim_assessment", include_args=False)` - Test function

### 4. Hierarchical Tracing

The implementation creates nested spans for better trace visualization:

```
test_claim_assessment
├── setup_tracing_environment
├── assess_claims_with_context
│   ├── claim_assessment_0
│   │   ├── assess_single_claim
│   │   │   ├── assess_single_claim_details
│   │   │   └── build_prompt_with_context
│   │   └── ...
│   ├── claim_assessment_1
│   └── claim_assessment_2
```

## Benefits

1. **Clean Code**: No manual span management scattered throughout functions
2. **Consistent Tracing**: All decorated functions follow the same tracing pattern
3. **Configurable**: Easy to control what gets traced and how
4. **Error Handling**: Automatic exception recording and error attribution
5. **Performance Insights**: Built-in duration and status tracking
6. **Maintainable**: Easy to add/remove tracing from functions

## Usage Examples

### Basic Usage
```python
@trace_function()
def simple_function():
    return "Hello World"
```

### Custom Span Name
```python
@trace_function("custom_operation_name")
def complex_function():
    # Implementation
    pass
```

### Sensitive Data Handling
```python
@trace_function(include_args=False, include_result=False)
def handle_sensitive_data(password, api_key):
    # Only function name and duration are traced
    pass
```

## Running the Application

### Poem Generation (Original)
```bash
python tracing_application.py
```

### Claim Assessment Test
```bash
python tracing_application.py test
```

## Trace Attributes

Each traced function automatically includes:
- `function.name` - Function name
- `function.module` - Module name
- `function.status` - success/error
- `function.args.*` - Function arguments (if enabled)
- `function.result.*` - Function result (if enabled)
- `function.error.*` - Error details (if exception occurs)

## Azure Monitor Integration

All traces are automatically sent to Azure Monitor Application Insights, providing:
- End-to-end request tracing
- Performance analytics
- Error tracking and alerting
- Custom dashboards and queries

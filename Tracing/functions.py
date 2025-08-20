import requests
from typing import Any, Callable, Set, Dict, List, Optional
import json
import os
from dotenv import load_dotenv

# OpenTelemetry imports for modern tracing
from opentelemetry import trace
from opentelemetry.trace import SpanKind

load_dotenv()

# Get tracer for this module
tracer = trace.get_tracer(__name__)


def get_weather(location: str) -> str:
    """
    Fetches the weather information for the specified location.

    :param location (str): The location to fetch weather for.
    :return: Weather information as a string of characters.
    :rtype: str
    """
    with tracer.start_as_current_span(
        "get_weather",
        kind=SpanKind.INTERNAL
    ) as span:
        # Add input parameters as span attributes
        span.set_attribute("function.name", "get_weather")
        span.set_attribute("function.parameters.location", location)
        
        try:
            # Fetch latitude and longitude of the specific location
            geocoding_url = (
                "http://api.openweathermap.org/geo/1.0/direct?q="
                + location
                + "&limit=1&appid=49d00b8f2cea3f44b13318df46f68364"
            )
            
            with tracer.start_as_current_span(
                "geocoding_api_call"
            ) as geo_span:
                geo_span.set_attribute("http.url", geocoding_url)
                response = requests.get(geocoding_url)
                geo_span.set_attribute(
                    "http.status_code", response.status_code
                )
                
                if response.status_code != 200:
                    error_msg = (
                        f"Geocoding API failed with status "
                        f"{response.status_code}"
                    )
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", error_msg)
                    return f"Error: {error_msg}"
                
                get_response = response.json()
                
                if not get_response:
                    error_msg = f"Location '{location}' not found"
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", error_msg)
                    return f"Error: {error_msg}"
                
                latitude = get_response[0]["lat"]
                longitude = get_response[0]["lon"]
                
                geo_span.set_attribute("geocoding.latitude", latitude)
                geo_span.set_attribute("geocoding.longitude", longitude)

            # Fetch weather data
            weather_url = (
                "https://api.openweathermap.org/data/2.5/weather?lat="
                + str(latitude)
                + "&lon="
                + str(longitude)
                + "&appid=49d00b8f2cea3f44b13318df46f68364"
            )
            
            with tracer.start_as_current_span(
                "weather_api_call"
            ) as weather_span:
                weather_span.set_attribute("http.url", weather_url)
                final_response = requests.get(weather_url)
                weather_span.set_attribute(
                    "http.status_code", final_response.status_code
                )
                
                if final_response.status_code != 200:
                    error_msg = (
                        f"Weather API failed with status "
                        f"{final_response.status_code}"
                    )
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", error_msg)
                    return f"Error: {error_msg}"
                
                final_response_json = final_response.json()
                weather = final_response_json["weather"][0]["description"]
                
                weather_span.set_attribute("weather.description", weather)
                weather_span.set_attribute(
                    "weather.temperature",
                    final_response_json.get("main", {}).get("temp")
                )
            
            # Set output attributes
            span.set_attribute("function.result", weather)
            span.set_attribute("success", True)
            
            return weather
            
        except Exception as e:
            # Record error in span
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.type", type(e).__name__)
            error_msg = f"Error fetching weather: {str(e)}"
            return error_msg


def get_user_info(user_id: int) -> str:
    """Retrieves user information based on user ID.

    :param user_id (int): ID of the user.
    :return: User information as a JSON string.
    :rtype: str
    """
    with tracer.start_as_current_span(
        "get_user_info",
        kind=SpanKind.INTERNAL
    ) as span:
        # Add input parameters as span attributes
        span.set_attribute("function.name", "get_user_info")
        span.set_attribute("function.parameters.user_id", user_id)
        
        try:
            mock_users = {
                1: {"name": "Alice", "email": "alice@example.com"},
                2: {"name": "Bob", "email": "bob@example.com"},
                3: {"name": "Charlie", "email": "charlie@example.com"},
            }
            
            user_info = mock_users.get(user_id, {"error": "User not found."})
            result = json.dumps({"user_info": user_info})
            
            # Set span attributes
            span.set_attribute("function.result", result)
            span.set_attribute("user.found", user_id in mock_users)
            span.set_attribute("success", True)
            
            if user_id in mock_users:
                span.set_attribute("user.name", user_info["name"])
                span.set_attribute("user.email", user_info["email"])
            
            return result
            
        except Exception as e:
            # Record error in span
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            span.set_attribute("error.type", type(e).__name__)
            error_result = json.dumps({"error": f"Error retrieving user info: {str(e)}"})
            return error_result


user_functions: Set[Callable[..., Any]] = {get_weather, get_user_info}

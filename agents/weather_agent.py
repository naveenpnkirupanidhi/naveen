"""
Weather Agent Module
Fetches weather data from WeatherAPI.com for location-based queries.
"""

import requests
from typing import Dict, Any, Optional
from datetime import datetime


class WeatherAgent:
    """
    Agent responsible for fetching and processing weather data.
    Uses WeatherAPI.com for real-time weather information.
    """

    def __init__(self, api_key: str):
        """
        Initialize the Weather Agent.

        Args:
            api_key: WeatherAPI.com API key
        """
        self.api_key = api_key
        self.base_url = "http://api.weatherapi.com/v1"

    def get_current_weather(self, location: str) -> dict:
        """
        Get current weather for a location.

        Args:
            location: City name, zip code, or coordinates

        Returns:
            Dictionary with weather data or error
        """
        result = {
            'location': '',
            'temperature_c': None,
            'temperature_f': None,
            'condition': '',
            'humidity': None,
            'wind_kph': None,
            'feels_like_c': None,
            'uv_index': None,
            'is_day': True,
            'raw_data': None,
            'error': None
        }

        try:
            url = f"{self.base_url}/current.json"
            params = {
                "key": self.api_key,
                "q": location,
                "aqi": "no"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract weather data
            current = data.get('current', {})
            location_data = data.get('location', {})

            result['location'] = f"{location_data.get('name', '')}, {location_data.get('country', '')}"
            result['temperature_c'] = current.get('temp_c')
            result['temperature_f'] = current.get('temp_f')
            result['condition'] = current.get('condition', {}).get('text', '')
            result['humidity'] = current.get('humidity')
            result['wind_kph'] = current.get('wind_kph')
            result['feels_like_c'] = current.get('feelslike_c')
            result['uv_index'] = current.get('uv')
            result['is_day'] = current.get('is_day', 1) == 1
            result['raw_data'] = data

        except requests.exceptions.Timeout:
            result['error'] = "Weather API request timed out. Please try again."
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                result['error'] = f"Invalid location: {location}"
            elif response.status_code == 401:
                result['error'] = "Invalid API key for weather service."
            else:
                result['error'] = f"Weather API error: {str(e)}"
        except requests.exceptions.RequestException as e:
            result['error'] = f"Network error: {str(e)}"
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"

        return result

    def get_forecast(self, location: str, days: int = 3) -> dict:
        """
        Get weather forecast for a location.

        Args:
            location: City name, zip code, or coordinates
            days: Number of forecast days (1-10)

        Returns:
            Dictionary with forecast data or error
        """
        result = {
            'location': '',
            'forecast_days': [],
            'error': None
        }

        try:
            url = f"{self.base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": location,
                "days": min(days, 10),
                "aqi": "no"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            location_data = data.get('location', {})
            result['location'] = f"{location_data.get('name', '')}, {location_data.get('country', '')}"

            forecast_data = data.get('forecast', {}).get('forecastday', [])

            for day in forecast_data:
                day_info = {
                    'date': day.get('date'),
                    'max_temp_c': day.get('day', {}).get('maxtemp_c'),
                    'min_temp_c': day.get('day', {}).get('mintemp_c'),
                    'avg_temp_c': day.get('day', {}).get('avgtemp_c'),
                    'condition': day.get('day', {}).get('condition', {}).get('text', ''),
                    'chance_of_rain': day.get('day', {}).get('daily_chance_of_rain'),
                    'uv_index': day.get('day', {}).get('uv')
                }
                result['forecast_days'].append(day_info)

        except requests.exceptions.RequestException as e:
            result['error'] = f"Weather API error: {str(e)}"
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"

        return result

    def format_weather(self, weather_data: dict) -> str:
        """
        Format weather data into a readable string.

        Args:
            weather_data: Weather data dictionary

        Returns:
            Formatted weather string
        """
        if weather_data.get('error'):
            return f"Weather Error: {weather_data['error']}"

        lines = []
        lines.append(f"Location: {weather_data['location']}")
        lines.append(f"Temperature: {weather_data['temperature_c']}C ({weather_data['temperature_f']}F)")
        lines.append(f"Feels Like: {weather_data['feels_like_c']}C")
        lines.append(f"Condition: {weather_data['condition']}")
        lines.append(f"Humidity: {weather_data['humidity']}%")
        lines.append(f"Wind: {weather_data['wind_kph']} km/h")
        lines.append(f"UV Index: {weather_data['uv_index']}")
        lines.append(f"Time: {'Day' if weather_data['is_day'] else 'Night'}")

        return "\n".join(lines)

    def format_forecast(self, forecast_data: dict) -> str:
        """
        Format forecast data into a readable string.

        Args:
            forecast_data: Forecast data dictionary

        Returns:
            Formatted forecast string
        """
        if forecast_data.get('error'):
            return f"Forecast Error: {forecast_data['error']}"

        lines = []
        lines.append(f"Weather Forecast for {forecast_data['location']}")
        lines.append("-" * 50)

        for day in forecast_data['forecast_days']:
            lines.append(f"\n{day['date']}:")
            lines.append(f"  High: {day['max_temp_c']}C / Low: {day['min_temp_c']}C")
            lines.append(f"  Condition: {day['condition']}")
            lines.append(f"  Chance of Rain: {day['chance_of_rain']}%")

        return "\n".join(lines)

    def is_good_for_outdoor(self, weather_data: dict) -> tuple:
        """
        Determine if weather is suitable for outdoor activities.

        Args:
            weather_data: Weather data dictionary

        Returns:
            Tuple of (is_good, reason)
        """
        if weather_data.get('error'):
            return False, "Unable to determine - weather data unavailable"

        temp = weather_data.get('temperature_c', 20)
        condition = weather_data.get('condition', '').lower()
        humidity = weather_data.get('humidity', 50)

        # Bad conditions
        bad_conditions = ['rain', 'storm', 'snow', 'sleet', 'thunder', 'heavy']
        if any(cond in condition for cond in bad_conditions):
            return False, f"Weather condition ({weather_data['condition']}) not suitable for outdoor activities"

        # Temperature check
        if temp < 10:
            return False, f"Temperature too cold ({temp}C) for comfortable outdoor activities"
        if temp > 35:
            return False, f"Temperature too hot ({temp}C) for outdoor activities"

        # Humidity check
        if humidity > 85:
            return False, f"Humidity too high ({humidity}%) for comfortable outdoor activities"

        return True, f"Good weather for outdoor activities ({weather_data['condition']}, {temp}C)"

    def query(self, question: str, location: str = None) -> dict:
        """
        Process a weather-related query.

        Args:
            question: Weather question
            location: Optional location (extracted from question if not provided)

        Returns:
            Dictionary with weather information
        """
        result = {
            'weather': None,
            'forecast': None,
            'formatted': '',
            'outdoor_suitable': None,
            'error': None
        }

        # Try to extract location from question if not provided
        if not location:
            # Simple location extraction - check for common patterns
            question_lower = question.lower()
            if 'in ' in question_lower:
                parts = question.split('in ')
                if len(parts) > 1:
                    location = parts[-1].strip().rstrip('?').strip()

        if not location:
            location = "New York"  # Default location

        # Determine what type of weather info is needed
        question_lower = question.lower()

        if 'forecast' in question_lower or 'tomorrow' in question_lower or 'next' in question_lower:
            forecast = self.get_forecast(location)
            result['forecast'] = forecast
            result['formatted'] = self.format_forecast(forecast)
            result['error'] = forecast.get('error')
        else:
            weather = self.get_current_weather(location)
            result['weather'] = weather
            result['formatted'] = self.format_weather(weather)
            result['outdoor_suitable'] = self.is_good_for_outdoor(weather)
            result['error'] = weather.get('error')

        return result


# Test the Weather Agent
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from config import WEATHER_API_KEY

    agent = WeatherAgent(WEATHER_API_KEY)

    # Test current weather
    print("=" * 60)
    print("Current Weather Test")
    print("=" * 60)
    result = agent.query("What's the weather in Singapore?")
    print(result['formatted'])

    if result['outdoor_suitable']:
        is_good, reason = result['outdoor_suitable']
        print(f"\nOutdoor Activities: {'Yes' if is_good else 'No'}")
        print(f"Reason: {reason}")

    # Test forecast
    print("\n" + "=" * 60)
    print("Weather Forecast Test")
    print("=" * 60)
    result = agent.query("What's the weather forecast for London?")
    print(result['formatted'])

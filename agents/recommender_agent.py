"""
Recommender Agent Module
Provides intelligent event recommendations based on weather and user preferences.
"""

import sqlite3
from openai import OpenAI
from typing import List, Dict, Any, Optional
from datetime import datetime

from .weather_agent import WeatherAgent


class RecommenderAgent:
    """
    Agent that recommends events based on weather conditions and user preferences.
    Combines weather data with event database to provide contextual recommendations.
    """

    def __init__(
        self,
        openai_api_key: str,
        weather_api_key: str,
        events_db_path: str = "events.db"
    ):
        """
        Initialize the Recommender Agent.

        Args:
            openai_api_key: OpenAI API key for GPT
            weather_api_key: WeatherAPI.com API key
            events_db_path: Path to the events database
        """
        self.openai_api_key = openai_api_key
        self.weather_agent = WeatherAgent(weather_api_key)
        self.events_db_path = events_db_path
        self.client = OpenAI(api_key=openai_api_key)

    def get_events(
        self,
        date: str = None,
        event_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events from the database.

        Args:
            date: Filter by date (YYYY-MM-DD format)
            event_type: Filter by type ('indoor' or 'outdoor')

        Returns:
            List of event dictionaries
        """
        conn = sqlite3.connect(self.events_db_path)
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM events WHERE 1=1"
            params = []

            if date:
                query += " AND date = ?"
                params.append(date)

            if event_type:
                query += " AND type = ?"
                params.append(event_type)

            query += " ORDER BY date, time"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            events = []
            for row in rows:
                events.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'description': row[3],
                    'location': row[4],
                    'date': row[5],
                    'time': row[6]
                })

            return events

        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return []
        finally:
            conn.close()

    def generate_recommendation(
        self,
        weather_data: dict,
        events: List[Dict[str, Any]],
        user_preference: str = None
    ) -> str:
        """
        Generate intelligent recommendations using GPT.

        Args:
            weather_data: Current weather information
            events: List of available events
            user_preference: Optional user preference (e.g., "outdoor", "family-friendly")

        Returns:
            Generated recommendation text
        """
        # Build context for GPT
        context_parts = []

        # Weather context
        if weather_data and not weather_data.get('error'):
            weather_context = f"""
Current Weather:
- Location: {weather_data.get('location', 'Unknown')}
- Temperature: {weather_data.get('temperature_c')}C ({weather_data.get('temperature_f')}F)
- Condition: {weather_data.get('condition')}
- Humidity: {weather_data.get('humidity')}%
- Feels Like: {weather_data.get('feels_like_c')}C
"""
            context_parts.append(weather_context)
        else:
            context_parts.append("Weather: Unable to retrieve weather data")

        # Events context
        if events:
            events_context = "\nAvailable Events:\n"
            for event in events:
                events_context += f"- {event['name']} ({event['type']})\n"
                events_context += f"  Description: {event['description']}\n"
                events_context += f"  Location: {event['location']}\n"
                events_context += f"  Time: {event['time']}\n\n"
            context_parts.append(events_context)
        else:
            context_parts.append("\nNo events found for the specified criteria.")

        # User preference
        if user_preference:
            context_parts.append(f"\nUser Preference: {user_preference}")

        full_context = "".join(context_parts)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful event recommender assistant.
Based on the weather conditions and available events, provide personalized recommendations.

Guidelines:
- Consider weather when recommending outdoor vs indoor activities
- Explain why certain events are recommended based on conditions
- If weather is bad for outdoor activities, prioritize indoor events
- Be specific about timing and practical considerations
- Keep recommendations concise but informative
- If user has preferences, prioritize those types of events"""
                    },
                    {
                        "role": "user",
                        "content": f"Please recommend events based on the following:\n{full_context}"
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Unable to generate recommendation: {str(e)}"

    def recommend(
        self,
        location: str,
        date: str = None,
        preference: str = None
    ) -> dict:
        """
        Main recommendation method that combines weather and events.

        Args:
            location: Location for weather lookup
            date: Date for events (defaults to today)
            preference: User preference for event types

        Returns:
            Dictionary with recommendation details
        """
        result = {
            'location': location,
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'weather': None,
            'events': [],
            'recommendation': '',
            'error': None
        }

        try:
            # Get weather data
            weather_result = self.weather_agent.get_current_weather(location)
            result['weather'] = weather_result

            # Get events for the date
            events = self.get_events(date=result['date'])
            result['events'] = events

            # Determine event type based on weather if no preference given
            if not preference and weather_result and not weather_result.get('error'):
                is_good, _ = self.weather_agent.is_good_for_outdoor(weather_result)
                if not is_good:
                    # Filter to indoor events if weather is bad
                    events = [e for e in events if e['type'] == 'indoor']
                    result['events'] = events

            # Generate recommendation
            recommendation = self.generate_recommendation(
                weather_result,
                events,
                preference
            )
            result['recommendation'] = recommendation

        except Exception as e:
            result['error'] = f"Recommendation error: {str(e)}"

        return result

    def format_recommendation(self, result: dict) -> str:
        """
        Format the recommendation result for display.

        Args:
            result: Recommendation result dictionary

        Returns:
            Formatted string
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"Event Recommendations for {result['location']}")
        lines.append(f"Date: {result['date']}")
        lines.append("=" * 60)

        if result.get('error'):
            lines.append(f"\nError: {result['error']}")
            return "\n".join(lines)

        # Weather summary
        weather = result.get('weather', {})
        if weather and not weather.get('error'):
            lines.append(f"\nWeather: {weather.get('condition')}, {weather.get('temperature_c')}C")
            is_good, reason = self.weather_agent.is_good_for_outdoor(weather)
            lines.append(f"Outdoor Suitability: {'Good' if is_good else 'Not Ideal'}")
        else:
            lines.append("\nWeather: Unavailable")

        # Events count
        events = result.get('events', [])
        lines.append(f"\nEvents Found: {len(events)}")

        # Recommendation
        lines.append("\n" + "-" * 60)
        lines.append("RECOMMENDATIONS:")
        lines.append("-" * 60)
        lines.append(result.get('recommendation', 'No recommendation available'))

        return "\n".join(lines)

    def query(self, question: str, location: str = None) -> dict:
        """
        Process a recommendation query.

        Args:
            question: User's question/request
            location: Optional location

        Returns:
            Dictionary with recommendation
        """
        # Extract location from question if not provided
        if not location:
            question_lower = question.lower()
            if 'in ' in question_lower:
                parts = question.split('in ')
                if len(parts) > 1:
                    location = parts[-1].strip().rstrip('?').strip()

        if not location:
            location = "Singapore"  # Default location

        # Determine preference from question
        preference = None
        question_lower = question.lower()
        if 'outdoor' in question_lower:
            preference = 'outdoor'
        elif 'indoor' in question_lower:
            preference = 'indoor'

        # Get recommendation
        result = self.recommend(location, preference=preference)
        result['formatted'] = self.format_recommendation(result)

        return result


# Test the Recommender Agent
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from config import OPENAI_API_KEY, WEATHER_API_KEY

    agent = RecommenderAgent(OPENAI_API_KEY, WEATHER_API_KEY)

    print("Testing Recommender Agent")
    print("=" * 60)

    result = agent.query("What events should I attend today in Singapore?")
    print(result['formatted'])

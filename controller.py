"""
Controller Module
Central orchestrator that routes user requests to appropriate agents.
Implements intent classification and multi-agent coordination.
"""

from openai import OpenAI
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.sql_agent import SQLAgent
from agents.rag_agent import RAGAgent
from agents.weather_agent import WeatherAgent
from agents.recommender_agent import RecommenderAgent
from agents.image_agent import ImageAgent


class ConversationMemory:
    """
    Simple conversation memory with limited window.
    Stores recent conversation turns for context.
    """

    def __init__(self, max_turns: int = 10):
        """
        Initialize conversation memory.

        Args:
            max_turns: Maximum number of turns to remember
        """
        self.max_turns = max_turns
        self.history: List[Dict[str, str]] = []

    def add_turn(self, user_input: str, assistant_response: str, agent_used: str):
        """Add a conversation turn to memory."""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'assistant': assistant_response,
            'agent': agent_used
        })

        # Trim to max_turns
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def get_context(self, num_turns: int = 5) -> str:
        """Get recent conversation context as string."""
        recent = self.history[-num_turns:] if self.history else []
        context_parts = []

        for turn in recent:
            context_parts.append(f"User: {turn['user']}")
            context_parts.append(f"Assistant: {turn['assistant'][:200]}...")

        return "\n".join(context_parts)

    def clear(self):
        """Clear conversation memory."""
        self.history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Get full conversation history."""
        return self.history.copy()


class Controller:
    """
    Main controller that orchestrates all agents.
    Routes user requests to the appropriate agent based on intent classification.
    """

    def __init__(
        self,
        openai_api_key: str,
        weather_api_key: str,
        memory_turns: int = 10
    ):
        """
        Initialize the Controller with all agents.

        Args:
            openai_api_key: OpenAI API key
            weather_api_key: WeatherAPI.com API key
            memory_turns: Number of conversation turns to remember
        """
        self.openai_api_key = openai_api_key
        self.weather_api_key = weather_api_key
        self.client = OpenAI(api_key=openai_api_key)

        # Initialize conversation memory
        self.memory = ConversationMemory(max_turns=memory_turns)

        # Initialize agents (lazy loading for efficiency)
        self._sql_agent = None
        self._rag_agent = None
        self._weather_agent = None
        self._recommender_agent = None
        self._image_agent = None

        # Agent categories for classification
        self.agent_descriptions = {
            'sql': 'Database queries about employees, departments, salaries, projects, budgets',
            'rag': 'Company policies, employee handbook, HR questions, benefits, PTO, leave policies',
            'weather': 'Weather information, temperature, forecast, conditions for any location',
            'recommend': 'Event recommendations, activity suggestions, what to do based on weather',
            'image': 'Generate images, create pictures, draw, visualize, make artwork',
            'general': 'General conversation, greetings, unclear requests'
        }

    @property
    def sql_agent(self) -> SQLAgent:
        """Lazy-load SQL agent."""
        if self._sql_agent is None:
            self._sql_agent = SQLAgent(self.openai_api_key)
        return self._sql_agent

    @property
    def rag_agent(self) -> RAGAgent:
        """Lazy-load RAG agent."""
        if self._rag_agent is None:
            self._rag_agent = RAGAgent(self.openai_api_key)
            self._rag_agent.initialize()
        return self._rag_agent

    @property
    def weather_agent(self) -> WeatherAgent:
        """Lazy-load Weather agent."""
        if self._weather_agent is None:
            self._weather_agent = WeatherAgent(self.weather_api_key)
        return self._weather_agent

    @property
    def recommender_agent(self) -> RecommenderAgent:
        """Lazy-load Recommender agent."""
        if self._recommender_agent is None:
            self._recommender_agent = RecommenderAgent(
                self.openai_api_key,
                self.weather_api_key
            )
        return self._recommender_agent

    @property
    def image_agent(self) -> ImageAgent:
        """Lazy-load Image agent."""
        if self._image_agent is None:
            self._image_agent = ImageAgent(self.openai_api_key)
        return self._image_agent

    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user intent to determine which agent to use.

        Args:
            user_input: User's input text

        Returns:
            Dictionary with 'agent', 'confidence', and 'reasoning'
        """
        # Get conversation context for better classification
        context = self.memory.get_context(3)

        prompt = f"""Classify the user's intent into one of these categories:
- sql: Database queries (employees, departments, salaries, projects, budgets)
- rag: Company policy questions (HR policies, benefits, PTO, handbook, leave)
- weather: Weather information requests
- recommend: Event or activity recommendations
- image: Image generation requests
- general: General conversation or unclear intent

Recent conversation context:
{context if context else 'No prior context'}

User input: "{user_input}"

Respond with a JSON object containing:
- "agent": the category name
- "confidence": number between 0 and 1
- "reasoning": brief explanation

JSON response:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )

            # Parse the response
            result_text = response.choices[0].message.content.strip()

            # Try to extract JSON from the response
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{[^}]+\}', result_text)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {'agent': 'general', 'confidence': 0.5, 'reasoning': 'Could not parse intent'}

            return result

        except Exception as e:
            return {
                'agent': 'general',
                'confidence': 0.0,
                'reasoning': f'Classification error: {str(e)}'
            }

    def route_to_agent(self, user_input: str, agent_name: str) -> dict:
        """
        Route the request to the appropriate agent.

        Args:
            user_input: User's input
            agent_name: Name of the agent to use

        Returns:
            Agent response dictionary
        """
        agent_map = {
            'sql': self.sql_agent,
            'rag': self.rag_agent,
            'weather': self.weather_agent,
            'recommend': self.recommender_agent,
            'image': self.image_agent
        }

        if agent_name not in agent_map:
            return self._handle_general(user_input)

        agent = agent_map[agent_name]

        try:
            result = agent.query(user_input)
            return result
        except Exception as e:
            return {'error': f'Agent error: {str(e)}', 'formatted': f'Error: {str(e)}'}

    def _handle_general(self, user_input: str) -> dict:
        """
        Handle general conversation that doesn't fit specific agents.

        Args:
            user_input: User's input

        Returns:
            Response dictionary
        """
        context = self.memory.get_context(3)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful AI assistant. You have access to:
- SQL Agent: For database queries about employees, departments, and projects
- RAG Agent: For company policy and employee handbook questions
- Weather Agent: For weather information
- Recommender Agent: For event and activity recommendations
- Image Agent: For generating images

If the user's request is unclear, ask for clarification.
If you can identify what they need, suggest which capability would help them."""
                    },
                    {
                        "role": "user",
                        "content": f"Previous context:\n{context}\n\nCurrent message: {user_input}"
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )

            answer = response.choices[0].message.content

            return {
                'answer': answer,
                'formatted': answer,
                'error': None
            }

        except Exception as e:
            return {
                'answer': f"I apologize, but I encountered an error: {str(e)}",
                'formatted': f"Error: {str(e)}",
                'error': str(e)
            }

    def process(self, user_input: str, force_agent: str = None) -> Dict[str, Any]:
        """
        Main method to process user input.

        Args:
            user_input: User's input text
            force_agent: Optional agent name to force routing

        Returns:
            Complete response with agent info and result
        """
        response = {
            'user_input': user_input,
            'timestamp': datetime.now().isoformat(),
            'intent': None,
            'agent_used': None,
            'result': None,
            'formatted_response': '',
            'error': None
        }

        try:
            # Classify intent (unless agent is forced)
            if force_agent:
                intent = {'agent': force_agent, 'confidence': 1.0, 'reasoning': 'Forced by user'}
            else:
                intent = self.classify_intent(user_input)

            response['intent'] = intent
            agent_name = intent.get('agent', 'general')
            response['agent_used'] = agent_name

            # Route to appropriate agent
            if agent_name == 'general':
                result = self._handle_general(user_input)
            else:
                result = self.route_to_agent(user_input, agent_name)

            response['result'] = result

            # Extract formatted response
            if 'formatted' in result:
                response['formatted_response'] = result['formatted']
            elif 'answer' in result:
                response['formatted_response'] = result['answer']
            elif 'error' in result and result['error']:
                response['formatted_response'] = f"Error: {result['error']}"
            else:
                response['formatted_response'] = str(result)

            # Add to memory
            self.memory.add_turn(
                user_input,
                response['formatted_response'],
                agent_name
            )

        except Exception as e:
            response['error'] = str(e)
            response['formatted_response'] = f"I apologize, but I encountered an error: {str(e)}"

        return response

    def get_capabilities(self) -> str:
        """Get a description of all available capabilities."""
        return """
Available Capabilities:
=======================

1. SQL Database Queries
   - Query employee information
   - Department and budget data
   - Project status and details
   Example: "What is the average salary by department?"

2. Document Q&A (RAG)
   - Employee handbook questions
   - Company policies
   - Benefits and PTO information
   Example: "How much PTO do I get?"

3. Weather Information
   - Current weather conditions
   - Weather forecasts
   - Outdoor activity suitability
   Example: "What's the weather in Singapore?"

4. Event Recommendations
   - Activity suggestions based on weather
   - Indoor/outdoor event recommendations
   Example: "What events should I attend today?"

5. Image Generation
   - Create images from text descriptions
   - Multiple artistic styles
   Example: "Generate an image of a sunset over mountains"
"""

    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
        if self._rag_agent:
            self._rag_agent.clear_memory()
        print("Conversation memory cleared.")


# Test the Controller
if __name__ == "__main__":
    from config import OPENAI_API_KEY, WEATHER_API_KEY

    controller = Controller(OPENAI_API_KEY, WEATHER_API_KEY)

    print(controller.get_capabilities())
    print("\n" + "=" * 60)

    # Test queries
    test_queries = [
        "What is the average salary in Engineering?",
        "How much PTO do I get as a new employee?",
        "What's the weather like in London?",
        "What events should I attend today in Singapore?",
        "Hello, how can you help me?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"User: {query}")
        print('='*60)

        response = controller.process(query)
        print(f"Agent Used: {response['agent_used']}")
        print(f"Response:\n{response['formatted_response']}")

"""
Integrated AI Assistant - Main Application
A unified conversational interface for multiple AI capabilities.

Features:
- Conversational interface with memory
- Document-based Q&A (RAG)
- SQL database queries
- Weather information
- Event recommendations
- Text-to-image generation

Author: Final Project Submission
Date: January 2026
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OPENAI_API_KEY, WEATHER_API_KEY
from controller import Controller
from database_setup import initialize_all_databases


def print_banner():
    """Print the application banner."""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║            INTEGRATED AI ASSISTANT                             ║
║            ========================                            ║
║                                                                ║
║    A Multi-Agent System for Enterprise Tasks                   ║
║                                                                ║
║    Capabilities:                                               ║
║    - SQL Database Queries                                      ║
║    - Document Q&A (RAG)                                        ║
║    - Weather Information                                       ║
║    - Event Recommendations                                     ║
║    - Image Generation                                          ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Print help information."""
    help_text = """
COMMANDS:
---------
  help     - Show this help message
  caps     - Show detailed capabilities
  clear    - Clear conversation memory
  history  - Show conversation history
  exit     - Exit the application

EXAMPLE QUERIES:
----------------
  SQL:      "What is the average salary by department?"
  RAG:      "How much PTO do I get as a new employee?"
  Weather:  "What's the weather in Singapore?"
  Recommend:"What events should I attend today?"
  Image:    "Generate an image of a sunset"

TIPS:
-----
  - The assistant automatically detects your intent
  - Follow-up questions use context from previous turns
  - Use 'clear' to start a fresh conversation
"""
    print(help_text)


def display_response(response: dict):
    """Display a formatted response."""
    print("\n" + "─" * 60)
    print(f"Agent: {response.get('agent_used', 'Unknown').upper()}")
    print("─" * 60)

    formatted = response.get('formatted_response', '')
    if formatted:
        print(formatted)
    else:
        print("No response generated.")

    print("─" * 60)


def run_demo_mode(controller: Controller):
    """Run a demonstration of all capabilities."""
    print("\n" + "=" * 60)
    print("DEMONSTRATION MODE")
    print("Running sample queries for each capability...")
    print("=" * 60)

    demo_queries = [
        ("SQL Agent", "What is the average salary in each department?"),
        ("RAG Agent", "How much PTO do I get as a new employee?"),
        ("RAG Agent (Follow-up)", "Does it roll over to the next year?"),
        ("Weather Agent", "What's the weather in London?"),
        ("Recommender Agent", "What events should I attend today in Singapore?"),
        ("General", "Hello! What can you help me with?")
    ]

    for agent_name, query in demo_queries:
        print(f"\n{'='*60}")
        print(f"[{agent_name}]")
        print(f"User: {query}")
        print("-" * 60)

        response = controller.process(query)
        print(f"Agent Used: {response['agent_used']}")
        print(f"\nResponse:\n{response['formatted_response'][:500]}")
        if len(response.get('formatted_response', '')) > 500:
            print("... [truncated]")

        print()
        input("Press Enter to continue...")

    print("\n" + "=" * 60)
    print("Demonstration complete!")
    print("=" * 60)


def main():
    """Main application entry point."""
    # Initialize databases if they don't exist
    if not os.path.exists('company.db') or not os.path.exists('events.db'):
        print("Initializing databases...")
        initialize_all_databases()
        print()

    # Print banner
    print_banner()

    # Initialize controller
    print("Initializing AI Assistant...")
    try:
        controller = Controller(OPENAI_API_KEY, WEATHER_API_KEY)
        print("AI Assistant ready!\n")
    except Exception as e:
        print(f"Error initializing assistant: {e}")
        return

    print("Type 'help' for commands, or start asking questions.")
    print("Type 'demo' to see a demonstration of all capabilities.")
    print()

    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == 'exit':
                print("\nThank you for using the AI Assistant. Goodbye!")
                break

            elif user_input.lower() == 'help':
                print_help()
                continue

            elif user_input.lower() == 'caps':
                print(controller.get_capabilities())
                continue

            elif user_input.lower() == 'clear':
                controller.clear_memory()
                print("Conversation memory cleared. Starting fresh!\n")
                continue

            elif user_input.lower() == 'history':
                history = controller.memory.get_history()
                if not history:
                    print("No conversation history yet.\n")
                else:
                    print("\nConversation History:")
                    print("-" * 40)
                    for i, turn in enumerate(history, 1):
                        print(f"\nTurn {i} ({turn['agent']}):")
                        print(f"  User: {turn['user'][:50]}...")
                        print(f"  Assistant: {turn['assistant'][:50]}...")
                    print()
                continue

            elif user_input.lower() == 'demo':
                run_demo_mode(controller)
                continue

            # Process the query
            response = controller.process(user_input)

            # Display the response
            display_response(response)

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit or continue chatting.")

        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


def run_notebook_demo():
    """
    Run a demonstration suitable for Jupyter notebooks.
    Returns formatted output for each capability.
    """
    # Initialize
    if not os.path.exists('company.db') or not os.path.exists('events.db'):
        initialize_all_databases()

    controller = Controller(OPENAI_API_KEY, WEATHER_API_KEY)

    results = {}

    # Test each capability
    test_cases = {
        'sql': [
            "What is the average salary in each department?",
            "Which employees earn more than 80000?",
            "What projects are currently in progress?"
        ],
        'rag': [
            "How much PTO do I get as a new employee?",
            "Does it roll over to the next year?",
            "What is the 401k matching policy?"
        ],
        'weather': [
            "What's the weather in Singapore?",
            "What's the forecast for London?"
        ],
        'recommend': [
            "What events should I attend today?"
        ]
    }

    for category, queries in test_cases.items():
        results[category] = []
        for query in queries:
            response = controller.process(query)
            results[category].append({
                'query': query,
                'agent': response['agent_used'],
                'response': response['formatted_response']
            })

    return results, controller


if __name__ == "__main__":
    main()

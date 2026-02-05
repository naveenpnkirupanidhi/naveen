"""
Flask Backend for Portfolio AI Agents
Provides API endpoints for each agent's chat functionality
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OPENAI_API_KEY, WEATHER_API_KEY
from agents.sql_agent import SQLAgent
from agents.rag_agent import RAGAgent
from agents.weather_agent import WeatherAgent
from agents.recommender_agent import RecommenderAgent
from agents.image_agent import ImageAgent

app = Flask(__name__, static_folder='.')
CORS(app)

# Get paths relative to parent directory (Final Assignment)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
handbook_path = os.path.join(parent_dir, "employee_handbook.txt")
print(f"Handbook path: {handbook_path}")
print(f"Exists: {os.path.exists(handbook_path)}")

# Initialize agents
print("Initializing agents...")
sql_agent = SQLAgent(OPENAI_API_KEY)
rag_agent = RAGAgent(OPENAI_API_KEY, document_path=handbook_path)
weather_agent = WeatherAgent(WEATHER_API_KEY)
recommender_agent = RecommenderAgent(OPENAI_API_KEY, WEATHER_API_KEY)
image_agent = ImageAgent(OPENAI_API_KEY)

# Initialize RAG agent
rag_agent.initialize()
print("All agents initialized!")


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/api/chat/sql', methods=['POST'])
def chat_sql():
    """SQL Agent endpoint"""
    try:
        data = request.json
        query = data.get('message', '')

        result = sql_agent.query(query)

        if result.get('error'):
            return jsonify({
                'success': False,
                'response': f"Error: {result['error']}"
            })

        response = f"**Generated SQL:**\n```sql\n{result.get('sql', 'N/A')}\n```\n\n**Results:**\n```\n{result.get('formatted', 'No results')}\n```"

        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f"Error: {str(e)}"
        })


@app.route('/api/chat/rag', methods=['POST'])
def chat_rag():
    """RAG Agent endpoint"""
    try:
        data = request.json
        query = data.get('message', '')

        result = rag_agent.query(query)

        if result.get('error'):
            return jsonify({
                'success': False,
                'response': f"Error: {result['error']}"
            })

        return jsonify({
            'success': True,
            'response': result.get('answer', 'No answer available')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f"Error: {str(e)}"
        })


@app.route('/api/chat/weather', methods=['POST'])
def chat_weather():
    """Weather Agent endpoint"""
    try:
        data = request.json
        query = data.get('message', '')

        result = weather_agent.query(query)

        if result.get('error'):
            return jsonify({
                'success': False,
                'response': f"Error: {result['error']}"
            })

        return jsonify({
            'success': True,
            'response': result.get('formatted', 'No weather data available')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f"Error: {str(e)}"
        })


@app.route('/api/chat/recommender', methods=['POST'])
def chat_recommender():
    """Recommender Agent endpoint"""
    try:
        data = request.json
        query = data.get('message', '')

        result = recommender_agent.query(query)

        if result.get('error'):
            return jsonify({
                'success': False,
                'response': f"Error: {result['error']}"
            })

        return jsonify({
            'success': True,
            'response': result.get('formatted', 'No recommendations available')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f"Error: {str(e)}"
        })


@app.route('/api/chat/image', methods=['POST'])
def chat_image():
    """Image Agent endpoint - returns enhanced prompt and optionally generates image"""
    try:
        data = request.json
        query = data.get('message', '')
        generate = data.get('generate', False)  # Only generate if explicitly requested

        if generate:
            result = image_agent.query(query)
            if result.get('error'):
                return jsonify({
                    'success': False,
                    'response': f"Error: {result['error']}"
                })

            response = result.get('formatted', '')
            if result.get('image_url'):
                response += f"\n\n![Generated Image]({result['image_url']})"

            return jsonify({
                'success': True,
                'response': response,
                'image_url': result.get('image_url')
            })
        else:
            # Just enhance the prompt without generating
            enhanced = image_agent.enhance_prompt(query)
            response = f"**Your prompt:** {query}\n\n**Enhanced prompt:**\n{enhanced}\n\n*Click 'Generate Image' to create this image (uses API credits)*"

            return jsonify({
                'success': True,
                'response': response,
                'enhanced_prompt': enhanced
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f"Error: {str(e)}"
        })


@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get list of available agents"""
    agents = [
        {
            'id': 'sql',
            'name': 'SQL Agent',
            'description': 'Query company database using natural language',
            'icon': 'database',
            'color': '#ff9966',
            'examples': [
                'What is the average salary by department?',
                'Which employees earn more than 80000?',
                'Show all projects in progress'
            ]
        },
        {
            'id': 'rag',
            'name': 'Document Q&A',
            'description': 'Ask questions about company policies',
            'icon': 'file-text',
            'color': '#66cccc',
            'examples': [
                'How much PTO do I get?',
                'What is the 401k matching policy?',
                'How do I report harassment?'
            ]
        },
        {
            'id': 'weather',
            'name': 'Weather Agent',
            'description': 'Get real-time weather information',
            'icon': 'cloud',
            'color': '#9966ff',
            'examples': [
                'What is the weather in Singapore?',
                'Weather forecast for London',
                'Is it good for outdoor activities in New York?'
            ]
        },
        {
            'id': 'recommender',
            'name': 'Event Recommender',
            'description': 'Get personalized event recommendations',
            'icon': 'calendar',
            'color': '#66ff99',
            'examples': [
                'What events should I attend today?',
                'Recommend indoor activities',
                'What to do this weekend in Singapore?'
            ]
        },
        {
            'id': 'image',
            'name': 'Image Generator',
            'description': 'Generate images with AI (DALL-E)',
            'icon': 'image',
            'color': '#ff6699',
            'examples': [
                'A sunset over mountains',
                'A futuristic city at night',
                'A cat sitting on a windowsill'
            ]
        }
    ]
    return jsonify(agents)


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Portfolio AI Agents Server")
    print("="*50)
    print("Open http://localhost:5000 in your browser")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)

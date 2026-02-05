"""
Configuration file for the Integrated AI Assistant
Contains all API keys and configuration settings
"""

import os

# ============================================
# API KEYS (loaded from environment variables)
# ============================================

# OpenAI API Key for GPT models and DALL-E
# Set via environment variable: OPENAI_API_KEY
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# WeatherAPI.com API Key for weather data
# Set via environment variable: WEATHER_API_KEY
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')

# ============================================
# MODEL CONFIGURATION
# ============================================

# LLM Settings
LLM_MODEL = "gpt-3.5-turbo"  # Can use "gpt-4" for better responses
LLM_TEMPERATURE = 0.3  # Lower = more focused, Higher = more creative
IMAGE_MODEL = "dall-e-3"  # For text-to-image generation

# Embedding Settings
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSIONS = 1536

# ============================================
# RAG CONFIGURATION
# ============================================

# Document chunking settings
CHUNK_SIZE = 2000  # Characters per chunk (~500 tokens)
CHUNK_OVERLAP = 200  # Overlap between chunks (~50 tokens)
RETRIEVAL_TOP_K = 3  # Number of documents to retrieve

# ============================================
# DATABASE CONFIGURATION
# ============================================

# SQLite database paths
COMPANY_DB_PATH = "company.db"
EVENTS_DB_PATH = "events.db"

# ============================================
# MEMORY CONFIGURATION
# ============================================

# Conversation memory settings
MAX_MEMORY_TURNS = 10  # Limit conversation history to last N turns
MEMORY_TYPE = "buffer"  # Options: "buffer", "summary", "window"

# ============================================
# AGENT CONFIGURATION
# ============================================

# Available agents in the system
AVAILABLE_AGENTS = [
    "sql",       # SQL database queries
    "rag",       # Document-based Q&A
    "weather",   # Weather information
    "recommend", # Event recommendations
    "image"      # Text-to-image generation
]

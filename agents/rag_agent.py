"""
RAG Agent Module
Retrieval-Augmented Generation for document-based question answering.
"""

import os
from typing import List, Dict, Any, Optional

# LangChain imports
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferWindowMemory

import warnings
warnings.filterwarnings('ignore')


class RAGAgent:
    """
    Agent for document-based question answering using Retrieval-Augmented Generation.
    Supports conversational memory for multi-turn interactions.
    """

    def __init__(
        self,
        api_key: str,
        document_path: str = "employee_handbook.txt",
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        retrieval_k: int = 3,
        memory_window: int = 5
    ):
        """
        Initialize the RAG Agent.

        Args:
            api_key: OpenAI API key
            document_path: Path to the document for RAG
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            retrieval_k: Number of documents to retrieve
            memory_window: Number of conversation turns to remember
        """
        os.environ["OPENAI_API_KEY"] = api_key
        self.api_key = api_key
        self.document_path = document_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retrieval_k = retrieval_k
        self.memory_window = memory_window

        self.vectorstore = None
        self.qa_chain = None
        self.memory = None
        self.is_initialized = False

    def initialize(self) -> bool:
        """
        Initialize the RAG system by loading documents and creating the vector store.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Check if document exists
            if not os.path.exists(self.document_path):
                print(f"Document not found: {self.document_path}")
                return False

            # Load document
            loader = TextLoader(self.document_path, encoding='utf-8')
            documents = loader.load()

            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)

            # Create embeddings and vector store
            embeddings = OpenAIEmbeddings()
            self.vectorstore = FAISS.from_documents(
                documents=chunks,
                embedding=embeddings
            )

            # Set up memory with window
            self.memory = ConversationBufferWindowMemory(
                k=self.memory_window,
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )

            # Create the conversational chain
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.3
            )

            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=self.vectorstore.as_retriever(
                    search_kwargs={"k": self.retrieval_k}
                ),
                memory=self.memory,
                return_source_documents=True,
                verbose=False
            )

            self.is_initialized = True
            print(f"RAG Agent initialized with {len(chunks)} document chunks.")
            return True

        except Exception as e:
            print(f"Error initializing RAG Agent: {str(e)}")
            return False

    def query(self, question: str) -> dict:
        """
        Query the RAG system with a question.

        Args:
            question: User's question

        Returns:
            Dictionary with 'answer', 'sources', and 'error' keys
        """
        result = {
            'answer': '',
            'formatted': '',
            'sources': [],
            'error': None
        }

        if not self.is_initialized:
            if not self.initialize():
                result['error'] = "RAG Agent not initialized. Document may be missing."
                return result

        try:
            response = self.qa_chain({"question": question})
            result['answer'] = response['answer']
            result['formatted'] = response['answer']

            # Extract source information
            if 'source_documents' in response:
                for doc in response['source_documents']:
                    source_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    result['sources'].append(source_preview)

        except Exception as e:
            result['error'] = f"Query error: {str(e)}"
            result['formatted'] = f"Error: {str(e)}"

        return result

    def clear_memory(self):
        """
        Clear the conversation memory to start fresh.
        """
        if self.memory:
            self.memory.clear()
            print("Conversation memory cleared.")

    def get_memory_context(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history from memory.

        Returns:
            List of conversation turns
        """
        if not self.memory:
            return []

        history = []
        memory_vars = self.memory.load_memory_variables({})

        if 'chat_history' in memory_vars:
            for msg in memory_vars['chat_history']:
                role = "user" if msg.type == "human" else "assistant"
                history.append({
                    "role": role,
                    "content": msg.content
                })

        return history

    def semantic_search(self, query: str, k: int = 3) -> List[str]:
        """
        Perform semantic search without generating an answer.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant document chunks
        """
        if not self.is_initialized:
            if not self.initialize():
                return []

        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []


# Test the RAG Agent
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from config import OPENAI_API_KEY

    agent = RAGAgent(OPENAI_API_KEY)

    if agent.initialize():
        test_questions = [
            "How much PTO do I get as a new employee?",
            "Does it roll over to the next year?",
            "What happens to my unused days if I leave the company?",
            "What is the 401k matching policy?",
            "How do I report harassment?"
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*60}")
            print(f"Turn {i}: {question}")
            print('='*60)

            result = agent.query(question)

            if result['error']:
                print(f"Error: {result['error']}")
            else:
                print(f"Answer: {result['answer']}")
                if result['sources']:
                    print(f"\nSources consulted: {len(result['sources'])} documents")

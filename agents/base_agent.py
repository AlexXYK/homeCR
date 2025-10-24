"""Base agent class with Gemini integration."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from config import settings


class AgentMessage:
    """Represents a message from an agent."""
    
    def __init__(self, role: str, content: str, metadata: Dict = None):
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""
    
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.conversation_history: List[AgentMessage] = []
        self.llm = None
        
        # Initialize LLM if Gemini is available and configured
        if GEMINI_AVAILABLE and settings.gemini_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    google_api_key=settings.gemini_api_key,
                    temperature=0.1,
                    max_output_tokens=4096
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini for {name}: {e}")
        
    def is_available(self) -> bool:
        """Check if the agent is ready to use."""
        return self.llm is not None
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history."""
        msg = AgentMessage(role, content, metadata)
        self.conversation_history.append(msg)
        return msg
    
    async def think(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Have the agent think about a problem using the LLM.
        
        Args:
            prompt: The prompt/question for the agent
            context: Optional context dictionary
            
        Returns:
            Agent's response
        """
        if not self.is_available():
            raise RuntimeError(
                f"Agent {self.name} is not available. "
                "Please set GEMINI_API_KEY in your .env file. "
                "Get a key at: https://ai.google.dev/"
            )
        
        # Build full prompt with system context
        full_prompt = f"""You are {self.name}, {self.role}.

{self.system_prompt}

Context: {json.dumps(context, indent=2) if context else 'None'}

Task: {prompt}

Respond thoughtfully and concisely:"""
        
        # Get response from LLM
        try:
            response = await self.llm.ainvoke(full_prompt)
            response_text = response.content
            
            # Log interaction
            self.add_message("user", prompt, {"context": context})
            self.add_message("assistant", response_text)
            
            return response_text
        except Exception as e:
            error_msg = f"Error in agent thinking: {e}"
            print(error_msg)
            raise
    
    @abstractmethod
    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a specific task.
        
        Args:
            task: Task dictionary with details
            
        Returns:
            Result dictionary
        """
        pass
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history as list of dictionaries."""
        return [msg.to_dict() for msg in self.conversation_history]
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


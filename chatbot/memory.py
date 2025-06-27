"""
Chat memory management for the decarbonization AI system.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    timestamp: datetime
    sender: str  # "user" or "assistant"
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatMemory:
    """Manages chat conversation history and context."""
    
    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self.messages: List[ChatMessage] = []
        self._lock = asyncio.Lock()
    
    async def add_message(self, sender: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Add a new message to the conversation history."""
        async with self._lock:
            chat_message = ChatMessage(
                timestamp=datetime.now(),
                sender=sender,
                message=message,
                context=context
            )
            
            self.messages.append(chat_message)
            
            # Keep only the most recent messages
            if len(self.messages) > self.max_messages:
                self.messages = self.messages[-self.max_messages:]
    
    async def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """Get the most recent messages."""
        async with self._lock:
            return self.messages[-count:] if self.messages else []
    
    async def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        async with self._lock:
            if not self.messages:
                return "No conversation history."
            
            user_messages = [msg.message for msg in self.messages if msg.sender == "user"]
            assistant_messages = [msg.message for msg in self.messages if msg.sender == "assistant"]
            
            summary = f"Conversation summary:\n"
            summary += f"- Total messages: {len(self.messages)}\n"
            summary += f"- User messages: {len(user_messages)}\n"
            summary += f"- Assistant messages: {len(assistant_messages)}\n"
            summary += f"- Duration: {self.messages[-1].timestamp - self.messages[0].timestamp}\n"
            
            return summary
    
    async def get_context_for_llm(self, max_context_messages: int = 5) -> str:
        """Get formatted conversation context for LLM."""
        async with self._lock:
            recent_messages = self.messages[-max_context_messages:] if self.messages else []
            
            if not recent_messages:
                return ""
            
            context = "Recent conversation:\n"
            for msg in recent_messages:
                role = "User" if msg.sender == "user" else "Assistant"
                context += f"{role}: {msg.message}\n"
            
            return context
    
    async def clear_memory(self) -> None:
        """Clear all conversation history."""
        async with self._lock:
            self.messages.clear()
    
    async def export_conversation(self, filename: str) -> None:
        """Export conversation to a JSON file."""
        async with self._lock:
            conversation_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_messages": len(self.messages),
                "messages": [
                    {
                        "timestamp": msg.timestamp.isoformat(),
                        "sender": msg.sender,
                        "message": msg.message,
                        "context": msg.context
                    }
                    for msg in self.messages
                ]
            }
            
            with open(filename, 'w') as f:
                json.dump(conversation_data, f, indent=2)
    
    async def import_conversation(self, filename: str) -> None:
        """Import conversation from a JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            async with self._lock:
                self.messages.clear()
                for msg_data in data.get("messages", []):
                    message = ChatMessage(
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        sender=msg_data["sender"],
                        message=msg_data["message"],
                        context=msg_data.get("context")
                    )
                    self.messages.append(message)
                    
        except Exception as e:
            print(f"Error importing conversation: {e}")
    
    async def search_messages(self, query: str) -> List[ChatMessage]:
        """Search for messages containing the query."""
        async with self._lock:
            matching_messages = []
            query_lower = query.lower()
            
            for msg in self.messages:
                if query_lower in msg.message.lower():
                    matching_messages.append(msg)
            
            return matching_messages
    
    async def get_message_stats(self) -> Dict[str, Any]:
        """Get statistics about the conversation."""
        async with self._lock:
            if not self.messages:
                return {"total_messages": 0, "user_messages": 0, "assistant_messages": 0}
            
            user_count = sum(1 for msg in self.messages if msg.sender == "user")
            assistant_count = sum(1 for msg in self.messages if msg.sender == "assistant")
            
            return {
                "total_messages": len(self.messages),
                "user_messages": user_count,
                "assistant_messages": assistant_count,
                "conversation_duration": str(self.messages[-1].timestamp - self.messages[0].timestamp),
                "average_message_length": sum(len(msg.message) for msg in self.messages) / len(self.messages)
            }


class ContextManager:
    """Manages context information for chat interactions."""
    
    def __init__(self):
        self.system_context: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def update_system_context(self, context: Dict[str, Any]) -> None:
        """Update system context information."""
        async with self._lock:
            self.system_context.update(context)
    
    async def get_system_context(self) -> Dict[str, Any]:
        """Get current system context."""
        async with self._lock:
            return self.system_context.copy()
    
    async def set_user_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        async with self._lock:
            self.user_preferences[key] = value
    
    async def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences."""
        async with self._lock:
            return self.user_preferences.copy()
    
    async def get_full_context(self) -> Dict[str, Any]:
        """Get full context including system and user preferences."""
        async with self._lock:
            return {
                "system": self.system_context.copy(),
                "user_preferences": self.user_preferences.copy(),
                "timestamp": datetime.now().isoformat()
            }


# Global instances
chat_memory = ChatMemory()
context_manager = ContextManager() 
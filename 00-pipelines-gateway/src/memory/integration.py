# 00-pipelines-gateway/src/memory/integration.py
"""
Memory 2.0 integration for OpenRouter refactor
Provides enhanced memory storage and retrieval for conversations
"""
import httpx
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Memory service endpoint
MEMORY_SERVICE_URL = os.getenv("MEMORY_SERVICE_URL", 
                              "http://02-memory-2.0:8002")
MEMORY_ENABLED = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
TIMEOUT_SECONDS = int(os.getenv("MEMORY_TIMEOUT", "10"))


class MemoryIntegration:
    """Handles integration with Memory 2.0 service"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT_SECONDS)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def store_conversation(self, 
                                conversation_id: str,
                                messages: List[Dict[str, Any]],
                                model_used: str,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store conversation in memory service
        
        Args:
            conversation_id: Unique conversation identifier
            messages: List of conversation messages
            model_used: Model that was used for generation
            metadata: Additional metadata to store
            
        Returns:
            True if storage was successful
        """
        payload = {
            "conversation_id": conversation_id,
            "messages": messages,
            "model_used": model_used,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        try:
            response = await self.client.post(
                f"{MEMORY_SERVICE_URL}/store",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            logger.info(f"Stored conversation {conversation_id} in memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store conversation {conversation_id}: {e}")
            return False
    
    async def retrieve_conversation(self, 
                                   conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation from memory service
        
        Args:
            conversation_id: Conversation identifier to retrieve
            
        Returns:
            Conversation data or None if not found
        """
        try:
            response = await self.client.get(
                f"{MEMORY_SERVICE_URL}/retrieve/{conversation_id}"
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            conversation = response.json()
            
            logger.info(f"Retrieved conversation {conversation_id} from memory")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation {conversation_id}: {e}")
            return None
    
    async def search_conversations(self, 
                                  query: str,
                                  limit: int = 10,
                                  model_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search conversations by content
        
        Args:
            query: Search query
            limit: Maximum number of results
            model_filter: Filter by model used
            
        Returns:
            List of matching conversations
        """
        params = {
            "query": query,
            "limit": limit
        }
        
        if model_filter:
            params["model"] = model_filter
        
        try:
            response = await self.client.get(
                f"{MEMORY_SERVICE_URL}/search",
                params=params
            )
            response.raise_for_status()
            
            results = response.json()
            logger.info(f"Found {len(results)} conversations matching '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []
    
    async def get_conversation_context(self, 
                                     conversation_id: str,
                                     max_messages: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent context for a conversation
        
        Args:
            conversation_id: Conversation identifier
            max_messages: Maximum number of recent messages to retrieve
            
        Returns:
            List of recent messages
        """
        try:
            response = await self.client.get(
                f"{MEMORY_SERVICE_URL}/context/{conversation_id}",
                params={"limit": max_messages}
            )
            
            if response.status_code == 404:
                return []
            
            response.raise_for_status()
            context = response.json()
            
            messages = context.get("messages", [])
            logger.info(f"Retrieved {len(messages)} context messages for {conversation_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get context for {conversation_id}: {e}")
            return []
    
    async def update_conversation_metadata(self,
                                         conversation_id: str,
                                         metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a conversation
        
        Args:
            conversation_id: Conversation identifier
            metadata: Metadata to update
            
        Returns:
            True if update was successful
        """
        payload = {
            "conversation_id": conversation_id,
            "metadata": metadata
        }
        
        try:
            response = await self.client.patch(
                f"{MEMORY_SERVICE_URL}/metadata/{conversation_id}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            logger.info(f"Updated metadata for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata for {conversation_id}: {e}")
            return False
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from memory
        
        Args:
            conversation_id: Conversation identifier to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            response = await self.client.delete(
                f"{MEMORY_SERVICE_URL}/delete/{conversation_id}"
            )
            response.raise_for_status()
            
            logger.info(f"Deleted conversation {conversation_id} from memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of memory service
        
        Returns:
            Health status information
        """
        try:
            response = await self.client.get(f"{MEMORY_SERVICE_URL}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "available": True,
                    "status": health_data.get("status", "unknown"),
                    "service": "memory-2.0"
                }
            else:
                return {
                    "available": False,
                    "error": f"Status {response.status_code}",
                    "service": "memory-2.0"
                }
                
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "service": "memory-2.0"
            }


# Global memory integration instance
_memory_integration = None


async def get_memory_integration() -> MemoryIntegration:
    """Get or create the global memory integration"""
    global _memory_integration
    if _memory_integration is None:
        _memory_integration = MemoryIntegration()
    return _memory_integration


async def store_conversation_async(conversation_id: str,
                                  messages: List[Dict[str, Any]],
                                  model_used: str,
                                  metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to store conversation"""
    async with MemoryIntegration() as memory:
        return await memory.store_conversation(
            conversation_id, messages, model_used, metadata
        )


async def get_conversation_context_async(conversation_id: str,
                                        max_messages: int = 20) -> List[Dict[str, Any]]:
    """Convenience function to get conversation context"""
    async with MemoryIntegration() as memory:
        return await memory.get_conversation_context(conversation_id, max_messages)


async def search_conversations_async(query: str,
                                    limit: int = 10,
                                    model_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convenience function to search conversations"""
    async with MemoryIntegration() as memory:
        return await memory.search_conversations(query, limit, model_filter)

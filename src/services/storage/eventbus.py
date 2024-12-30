import asyncio
from typing import Any, Callable, Dict, Optional, Set, List, Tuple
from src.services.storage.base import BaseStorageService


class EventBusService(BaseStorageService):
    """
    Simple in-memory event bus service implementing BaseStorageService.
    Focuses solely on event pub/sub functionality while maintaining compatibility
    with the storage service interface.
    """

    def __init__(self, **kwargs: Dict[str, Any]):
        super().__init__(**kwargs)
        self._subscribers: Dict[str, Set[Callable[[Any], None]]] = {}

    async def connect(self) -> None:
        """No connection needed for in-memory event bus."""
        pass

    async def disconnect(self) -> None:
        """No disconnection needed for in-memory event bus."""
        self._subscribers.clear()

    # Event Bus Specific Operations
    async def publish(self, channel: str, message: Any) -> None:
        """
        Publish a message to all subscribers of a channel.

        Args:
            channel (str): The channel to publish to
            message (Any): The message to publish
        """
        if channel in self._subscribers:
            for subscriber in self._subscribers[channel]:
                asyncio.create_task(subscriber(message))

    async def subscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to a channel.

        Args:
            channel (str): The channel to subscribe to
            callback (Callable[[Any], None]): The callback to execute on messages
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
        self._subscribers[channel].add(callback)

    async def unsubscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from a channel.

        Args:
            channel (str): The channel to unsubscribe from
            callback (Callable[[Any], None]): The callback to remove
        """
        if channel in self._subscribers:
            self._subscribers[channel].discard(callback)

    async def is_healthy(self) -> bool:
        """Event bus is always healthy when in memory."""
        return True

    # Inherited Abstract Methods (Not Supported)
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        raise NotImplementedError("EventBus does not support key-value operations")

    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError("EventBus does not support key-value operations")

    async def delete(self, key: str) -> None:
        raise NotImplementedError("EventBus does not support key-value operations")

    async def list_push(self, key: str, value: Any, right: bool = True) -> None:
        raise NotImplementedError("EventBus does not support list operations")

    async def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        raise NotImplementedError("EventBus does not support list operations")

    async def set_add(self, key: str, *values: Any) -> None:
        raise NotImplementedError("EventBus does not support set operations")

    async def set_members(self, key: str) -> Set[Any]:
        raise NotImplementedError("EventBus does not support set operations")

    async def hash_set(self, key: str, field: str, value: Any) -> None:
        raise NotImplementedError("EventBus does not support hash operations")

    async def hash_get(self, key: str, field: str) -> Optional[Any]:
        raise NotImplementedError("EventBus does not support hash operations")

    # Add these methods to implement BaseService
    async def start(self) -> None:
        """Start the event bus service."""
        await self.connect()

    async def stop(self) -> None:
        """Stop the event bus service."""
        await self.disconnect()

    # Add these vector-related method implementations
    async def create_vector_index(
        self, index_name: str, vector_dimensions: int
    ) -> None:
        """Vector operations not supported in EventBus."""
        raise NotImplementedError("EventBus does not support vector operations")

    async def add_vector(
        self, index_name: str, key: str, vector: List[float], content: str, tag: str
    ) -> None:
        """Vector operations not supported in EventBus."""
        raise NotImplementedError("EventBus does not support vector operations")

    async def vector_knn_search(
        self, index_name: str, query_vector: List[float], top_k: int, tag: str
    ) -> List[Tuple[str, str, float]]:
        """Vector operations not supported in EventBus."""
        raise NotImplementedError("EventBus does not support vector operations")

    async def vector_range_search(
        self, index_name: str, query_vector: List[float], radius: float, tag: str
    ) -> List[Tuple[str, str, float]]:
        """Vector operations not supported in EventBus."""
        raise NotImplementedError("EventBus does not support vector operations")

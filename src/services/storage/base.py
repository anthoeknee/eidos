from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Set


class BaseStorageService(ABC):
    """
    Abstract base class for all storage services.
    """

    def __init__(self, **kwargs: Dict[str, Any]):
        """
        Initialize the storage service.

        Args:
            **kwargs: Keyword arguments for service initialization.
        """
        self.config = kwargs

    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to the storage service.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the storage service.
        """
        pass

    # Core Key-Value Operations
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value with optional TTL.

        Args:
            key (str): The key to set.
            value (Any): The value to set.
            ttl (Optional[int]): Time to live for the key in seconds.
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value.

        Args:
            key (str): The key to get.

        Returns:
            Optional[Any]: The value associated with the key, or None if not found.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete a value.

        Args:
            key (str): The key to delete.
        """
        pass

    # List Operations
    @abstractmethod
    async def list_push(self, key: str, value: Any, right: bool = True) -> None:
        """
        Push a value to a list (left or right).

        Args:
            key (str): The key to push to.
            value (Any): The value to push.
            right (bool): True if pushing to the right, False if pushing to the left.
        """
        pass

    @abstractmethod
    async def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        Get a range of values from a list.

        Args:
            key (str): The key to get the range from.
            start (int): The start index of the range.
            end (int): The end index of the range.

        Returns:
            List[Any]: The values in the specified range.
        """
        pass

    # Set Operations
    @abstractmethod
    async def set_add(self, key: str, *values: Any) -> None:
        """
        Add values to a set.

        Args:
            key (str): The key to add values to.
            *values (Any): The values to add.
        """
        pass

    @abstractmethod
    async def set_members(self, key: str) -> Set[Any]:
        """
        Get all members of a set.

        Args:
            key (str): The key to get the members of.

        Returns:
            Set[Any]: The members of the set.
        """
        pass

    # Hash Operations
    @abstractmethod
    async def hash_set(self, key: str, field: str, value: Any) -> None:
        """
        Set a hash field.

        Args:
            key (str): The key to set the hash field for.
            field (str): The field to set.
            value (Any): The value to set.
        """
        pass

    @abstractmethod
    async def hash_get(self, key: str, field: str) -> Optional[Any]:
        """
        Get a hash field.

        Args:
            key (str): The key to get the hash field from.
            field (str): The field to get.

        Returns:
            Optional[Any]: The value associated with the hash field, or None if not found.
        """
        pass

    # Pub/Sub Operations
    @abstractmethod
    async def publish(self, channel: str, message: Any) -> None:
        """
        Publish a message to a channel.

        Args:
            channel (str): The channel to publish the message to.
            message (Any): The message to publish.
        """
        pass

    @abstractmethod
    async def subscribe(self, channel: str, callback: callable) -> None:
        """
        Subscribe to a channel.

        Args:
            channel (str): The channel to subscribe to.
            callback (callable): The callback function to call when a message is received.
        """
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        """
        Check service health.

        Returns:
            bool: True if the service is healthy, False otherwise.
        """
        pass

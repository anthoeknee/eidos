from enum import Enum
from typing import Dict, Optional, Type
from src.services.storage.base import BaseStorageService
from src.services.storage.valkey import ValkeyService
from src.services.storage.eventbus import EventBusService


class StorageType(Enum):
    """Enum for different storage service types."""

    VALKEY = "valkey"
    EVENT_BUS = "event_bus"


class StorageFactory:
    """Factory for creating and managing storage service instances."""

    _instances: Dict[StorageType, BaseStorageService] = {}
    _service_map: Dict[StorageType, Type[BaseStorageService]] = {
        StorageType.VALKEY: ValkeyService,
        StorageType.EVENT_BUS: EventBusService,
    }

    @classmethod
    async def get_storage(
        cls, storage_type: StorageType, **kwargs
    ) -> BaseStorageService:
        """
        Get or create a storage service instance.

        Args:
            storage_type: Type of storage service to get/create
            **kwargs: Additional configuration for the storage service

        Returns:
            Instance of the requested storage service
        """
        if storage_type not in cls._instances:
            service_class = cls._service_map[storage_type]
            instance = service_class(**kwargs)
            await instance.connect()
            cls._instances[storage_type] = instance

        return cls._instances[storage_type]

    @classmethod
    async def shutdown(cls) -> None:
        """Gracefully shutdown all storage services."""
        for instance in cls._instances.values():
            await instance.disconnect()
        cls._instances.clear()


# Global storage instances for easy access
_valkey: Optional[ValkeyService] = None
_event_bus: Optional[EventBusService] = None


async def init_storage(**kwargs) -> None:
    """Initialize all storage services."""
    global _valkey, _event_bus

    from src.utils.logger import Logger

    logger = Logger(name="Storage", level="DEBUG")

    logger.debug("Initializing Valkey storage...")
    _valkey = await StorageFactory.get_storage(StorageType.VALKEY, **kwargs)
    logger.debug("Valkey storage initialized")

    logger.debug("Initializing Event Bus storage...")
    _event_bus = await StorageFactory.get_storage(StorageType.EVENT_BUS, **kwargs)
    logger.debug("Event Bus storage initialized")


async def shutdown_storage() -> None:
    """Shutdown all storage services."""
    await StorageFactory.shutdown()


def get_valkey() -> ValkeyService:
    """Get the Valkey storage service instance."""
    if _valkey is None:
        raise RuntimeError("Valkey storage service not initialized")
    return _valkey


def get_event_bus() -> EventBusService:
    """Get the Event Bus storage service instance."""
    if _event_bus is None:
        raise RuntimeError("Event Bus storage service not initialized")
    return _event_bus

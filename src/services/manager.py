import asyncio
from typing import Dict, Type
from src.services.base import BaseService
from src.services.storage.base import BaseStorageService


class ServiceManager:
    """
    Manages the lifecycle of all services.
    """

    def __init__(self):
        """
        Initialize the service manager.
        """
        self.services: Dict[str, BaseService] = {}

    def register(self, name: str, service_class: Type[BaseService], **kwargs):
        """
        Register a service with the manager.

        Args:
            name (str): The name of the service.
            service_class (Type[BaseService]): The class of the service.
            **kwargs: Keyword arguments for service initialization.
        """
        if name in self.services:
            raise ValueError(f"Service with name '{name}' already registered.")
        self.services[name] = service_class(**kwargs)

    async def start_all(self):
        """
        Start all registered services.
        """
        await asyncio.gather(*[service.start() for service in self.services.values()])
        # Connect to storage services
        await asyncio.gather(
            *[
                service.connect()
                for service in self.services.values()
                if isinstance(service, BaseStorageService)
            ]
        )

    async def stop_all(self):
        """
        Stop all registered services.
        """
        # Disconnect from storage services
        await asyncio.gather(
            *[
                service.disconnect()
                for service in self.services.values()
                if isinstance(service, BaseStorageService)
            ]
        )
        await asyncio.gather(*[service.stop() for service in self.services.values()])

    async def check_health(self) -> Dict[str, bool]:
        """
        Check the health of all registered services.

        Returns:
            Dict[str, bool]: A dictionary of service names and their health status.
        """
        health_status = await asyncio.gather(
            *[service.is_healthy() for service in self.services.values()]
        )
        return dict(zip(self.services.keys(), health_status))

    def get_service(self, name: str) -> BaseService:
        """
        Get a service by its name.

        Args:
            name (str): The name of the service.

        Returns:
            BaseService: The service instance.
        """
        if name not in self.services:
            raise ValueError(f"Service with name '{name}' not found.")
        return self.services[name]

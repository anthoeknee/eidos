from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


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
    async def start(self) -> None:
        """
        Start the service.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the service.
        """
        pass

    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to the storage.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the storage.
        """
        pass

    @abstractmethod
    async def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """
        Create a table in the storage.

        Args:
            table_name (str): The name of the table.
            columns (Dict[str, str]): A dictionary of column names and their types.
        """
        pass

    @abstractmethod
    async def insert(self, table_name: str, data: Dict[str, Any]) -> None:
        """
        Insert data into a table.

        Args:
            table_name (str): The name of the table.
            data (Dict[str, Any]): A dictionary of column names and their values.
        """
        pass

    @abstractmethod
    async def get_by_id(self, table_name: str, id: Any) -> Optional[Dict[str, Any]]:
        """
        Get a record by its ID.

        Args:
            table_name (str): The name of the table.
            id (Any): The ID of the record to get.

        Returns:
            Optional[Dict[str, Any]]: The record, or None if not found.
        """
        pass

    @abstractmethod
    async def update(self, table_name: str, id: Any, data: Dict[str, Any]) -> None:
        """
        Update a record in a table.

        Args:
            table_name (str): The name of the table.
            id (Any): The ID of the record to update.
            data (Dict[str, Any]): A dictionary of column names and their new values.
        """
        pass

    @abstractmethod
    async def delete(self, table_name: str, id: Any) -> None:
        """
        Delete a record from a table.

        Args:
            table_name (str): The name of the table.
            id (Any): The ID of the record to delete.
        """
        pass

    @abstractmethod
    async def list(
        self, table_name: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List records from a table.

        Args:
            table_name (str): The name of the table.
            limit (int): The maximum number of records to return.
            offset (int): The number of records to skip.

        Returns:
            List[Dict[str, Any]]: A list of records.
        """
        pass

    @abstractmethod
    async def query(
        self, sql: str, params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query.

        Args:
            sql (str): The SQL query to execute.
            params (Optional[List[Any]]): Parameters for the query.

        Returns:
            List[Dict[str, Any]]: A list of records.
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

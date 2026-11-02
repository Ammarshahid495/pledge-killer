"""
Storage Driver Abstraction for Pledge Fighter.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import hashlib
import os
import uuid


class StorageDriver(ABC):
    @abstractmethod
    def save_file(self, content: bytes, extension: str = ".cpp") -> Tuple[str, str, int]:
        """
        Saves file content securely.
        Returns (storage_key, sha256_hash, file_size_bytes).
        """
        pass

    @abstractmethod
    def get_file_content(self, storage_key: str) -> Optional[bytes]:
        """
        Retrieves file content by storage key.
        """
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """
        Deletes a stored file.
        """
        pass

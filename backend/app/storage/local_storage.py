"""
Local Filesystem Storage Driver.
Uses cryptographically random UUID storage keys so storage keys never reveal user identities or filenames.
"""

import hashlib
import os
import uuid
from typing import Optional, Tuple
from .storage_driver import StorageDriver
from ..core.config import settings


class LocalStorageDriver(StorageDriver):
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or settings.LOCAL_STORAGE_DIR
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, content: bytes, extension: str = ".cpp") -> Tuple[str, str, int]:
        sha256 = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        # Generate opaque storage key (no predictable user or submission info)
        storage_key = f"{uuid.uuid4().hex}{extension}"
        target_path = os.path.join(self.base_dir, storage_key)

        with open(target_path, "wb") as f:
            f.write(content)

        return storage_key, sha256, file_size

    def get_file_content(self, storage_key: str) -> Optional[bytes]:
        # Basic traversal security check
        clean_key = os.path.basename(storage_key)
        target_path = os.path.join(self.base_dir, clean_key)

        if not os.path.exists(target_path):
            return None

        with open(target_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_key: str) -> bool:
        clean_key = os.path.basename(storage_key)
        target_path = os.path.join(self.base_dir, clean_key)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                return True
            except OSError:
                return False
        return False


def get_storage_driver() -> StorageDriver:
    return LocalStorageDriver()

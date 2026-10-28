import json
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def read(self, path):
        raise NotImplementedError


class JsonStorage(StorageBackend):
    def read(self, path):
        with open(path) as f:
            return json.load(f)


class StorageFactory:
    _backends = {"json": JsonStorage}

    @classmethod
    def create(cls, kind="json"):
        return cls._backends[kind]()


def load_items(path):
    """Load inventory items from a JSON file."""
    backend = StorageFactory.create("json")
    return backend.read(path)

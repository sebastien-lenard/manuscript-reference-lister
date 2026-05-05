from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, fields
from typing import Self


@dataclass
class BaseSchema(ABC):
    """Base class providing common serialization methods for metadata."""

    def to_dict(self) -> dict:
        """Converts the instance into a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Creates an instance while ignoring extra keys not defined in the schema."""
        # This dynamically finds the fields for whatever class calls it
        class_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in class_fields})

    @property
    @abstractmethod
    def identity_key(self):
        """Return a unique identifier for deduplication."""
        raise NotImplementedError("Subclasses must implement identity_key")

    # TODO: add an abstract property get_update_status to be able to implement
    # different levels of update, like in JournalRepository::update_all(), rather
    # than using "if None in astuple(record)"

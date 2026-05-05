from dataclasses import dataclass

import pytest

from manuscript_reference_lister.schemas.base_schema import BaseSchema


@dataclass
class MockSchema(BaseSchema):
    name: str
    value: int = 0

    @property
    def identity_key(self):
        return self.name


def test_base_schema_to_dict() -> None:
    """Should be able to convert into a dict."""
    obj = MockSchema(name="Test", value=10)
    expected = {"name": "Test", "value": 10}
    assert obj.to_dict() == expected


def test_base_schema_from_dict_ignores_extra_fields() -> None:
    """Extra fields shouldn't raise errors."""
    raw_data = {"name": "Test", "value": 42, "extra_garbage": "ignore_me"}

    # This should NOT raise a TypeError
    obj = MockSchema.from_dict(raw_data)

    assert obj.name == "Test"
    assert obj.value == 42
    assert not hasattr(obj, "extra_garbage")


def test_base_schema_abstract_requirement() -> None:
    """Ensure you can't use a subclass without implementing identity_key."""

    @dataclass
    class BrokenSchema(BaseSchema):
        name: str

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BrokenSchema(name="Fail")

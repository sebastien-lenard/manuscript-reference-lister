import pytest

from manuscript_reference_lister.schemas.base_schema import BaseSchema


class MockSchema(BaseSchema):
    """Simple implementation for testing BaseSchema logic."""

    name: str
    value: int = 0

    @property
    def identity_key(self):
        return self.name


def test_base_schema_to_dict() -> None:
    """Should be able to convert into a dict."""
    obj = MockSchema(name="Test", value=10)
    expected = {"name": "Test", "value": 10}

    assert obj.model_dump() == expected


def test_base_schema_from_dict_ignores_extra_fields() -> None:
    """Extra fields shouldn't raise errors due to model_config extra='ignore'."""
    raw_data = {"name": "Test", "value": 42, "extra_garbage": "ignore_me"}

    obj = MockSchema(**raw_data)

    assert obj.name == "Test"
    assert obj.value == 42
    assert not hasattr(obj, "extra_garbage")


def test_base_schema_identity_key_requirement() -> None:
    """Ensure a subclass must implement identity_key or raise NotImplementedError."""

    class BrokenSchema(BaseSchema):
        name: str

    obj = BrokenSchema(name="Fail")

    with pytest.raises(
        NotImplementedError, match="Subclasses must implement identity_key"
    ):
        _ = obj.identity_key

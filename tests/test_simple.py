"""Simple test."""
import pytest

def test_simple():
    assert True

@pytest.mark.asyncio
async def test_async():
    assert True

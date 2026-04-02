import httpx
import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from src.foundation._012_serializers.router import router


app = FastAPI()
app.include_router(router)


@pytest.fixture
def client():
    return AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_serialize_csv(client):
    response = await client.post(
        "/api/v1/serialize/csv",
        json={
            "data": [{"name": "Alice", "age": 30}],
            "format": "csv",
            "include_bom": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert data["content"] == "name,age\nAlice,30\n"
    assert data["content_type"] == "text/csv"
    assert data["row_count"] == 1


@pytest.mark.asyncio
async def test_serialize_json(client):
    response = await client.post(
        "/api/v1/serialize/json",
        json={
            "data": {"key": "value"},
            "format": "json",
            "pretty": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["content"] == '{"key": "value"}'
    assert data["content_type"] == "application/json"


@pytest.mark.asyncio
async def test_serialize_xml(client):
    response = await client.post(
        "/api/v1/serialize/xml",
        json={
            "data": {"name": "Alice"},
            "format": "xml",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "xml"
    assert "<root><name>Alice</name></root>" in data["content"]
    assert data["content_type"] == "application/xml"


@pytest.mark.asyncio
async def test_deserialize_csv(client):
    response = await client.post(
        "/api/v1/serialize/deserialize/csv",
        json={
            "content": "name,age\nAlice,30\n",
            "format": "csv",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert data["data"] == [{"name": "Alice", "age": 30}]
    assert data["row_count"] == 1


@pytest.mark.asyncio
async def test_deserialize_json(client):
    response = await client.post(
        "/api/v1/serialize/deserialize/json",
        json={
            "content": '{"key": "value"}',
            "format": "json",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["data"] == {"key": "value"}


@pytest.mark.asyncio
async def test_deserialize_xml(client):
    response = await client.post(
        "/api/v1/serialize/deserialize/xml",
        json={
            "content": "<root><name>Alice</name></root>",
            "format": "xml",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "xml"
    assert data["data"] == {"name": "Alice"}


@pytest.mark.asyncio
async def test_flatten(client):
    response = await client.post(
        "/api/v1/serialize/flatten",
        json={
            "data": {"a": {"b": 1}},
            "separator": ".",
            "max_depth": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["original_keys"] == 1
    assert data["flattened_keys"] == 1
    assert data["data"] == {"a.b": 1}

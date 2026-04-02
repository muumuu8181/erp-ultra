import pytest
from src.foundation._008_cache.service import clear_cache_state

@pytest.fixture(autouse=True)
def setup_teardown():
    clear_cache_state()
    yield
    clear_cache_state()


@pytest.mark.asyncio
async def test_set_cache_endpoint(client):
    payload = {
        "key": "inventory:router:1", # Note: router overwrites from path
        "value": '{"msg": "test"}',
        "ttl_seconds": 3600,
        "module": "inventory"
    }

    response = await client.put("/api/v1/cache/inventory:router:1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "inventory:router:1"
    assert data["value"] == '{"msg": "test"}'
    assert data["module"] == "inventory"


@pytest.mark.asyncio
async def test_get_cache_endpoint(client):
    payload = {
        "key": "inventory:router:2",
        "value": '{"msg": "test"}',
        "ttl_seconds": 3600,
        "module": "inventory"
    }
    await client.put("/api/v1/cache/inventory:router:2", json=payload)

    response = await client.get("/api/v1/cache/inventory:router:2")
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "inventory:router:2"


@pytest.mark.asyncio
async def test_get_cache_not_found(client):
    response = await client.get("/api/v1/cache/nonexistent:key:123")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_cache_endpoint(client):
    payload = {
        "key": "inventory:router:del",
        "value": '{"msg": "test"}',
        "ttl_seconds": 3600,
        "module": "inventory"
    }
    await client.put("/api/v1/cache/inventory:router:del", json=payload)

    response = await client.delete("/api/v1/cache/inventory:router:del")
    assert response.status_code == 200

    get_response = await client.get("/api/v1/cache/inventory:router:del")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_clear_by_module_endpoint(client):
    payload = {
        "key": "inventory:router:clr",
        "value": '{"msg": "test"}',
        "ttl_seconds": 3600,
        "module": "inventory"
    }
    await client.put("/api/v1/cache/inventory:router:clr", json=payload)

    response = await client.delete("/api/v1/cache/?module=inventory")
    assert response.status_code == 200
    assert response.json()["cleared_count"] == 1


@pytest.mark.asyncio
async def test_invalidate_endpoint(client):
    payload = {
        "key": "inventory:router:inv",
        "value": '{"msg": "test"}',
        "ttl_seconds": 3600,
        "module": "inventory"
    }
    await client.put("/api/v1/cache/inventory:router:inv", json=payload)

    response = await client.post("/api/v1/cache/invalidate", json={"pattern": "inventory:*"})
    assert response.status_code == 200
    assert response.json()["invalidated_count"] == 1


@pytest.mark.asyncio
async def test_stats_endpoint(client):
    payload = {
        "key": "inventory:router:stat",
        "value": '{"msg": "test"}',
        "ttl_seconds": 3600,
        "module": "inventory"
    }
    await client.put("/api/v1/cache/inventory:router:stat", json=payload)
    await client.get("/api/v1/cache/inventory:router:stat")

    response = await client.get("/api/v1/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    inventory_stats = next(s for s in data if s["module"] == "inventory")
    assert inventory_stats["total_hits"] == 1


@pytest.mark.asyncio
async def test_warm_endpoint(client):
    payload = {
        "entries": [
            {
                "key": "inventory:warm:1",
                "value": '{"a": 1}',
                "ttl_seconds": 3600,
                "module": "inventory"
            },
            {
                "key": "inventory:warm:2",
                "value": '{"a": 2}',
                "ttl_seconds": 3600,
                "module": "inventory"
            }
        ]
    }
    response = await client.post("/api/v1/cache/warm", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_cleanup_endpoint(client):
    payload = {
        "key": "inventory:clean:1",
        "value": '{"msg": "test"}',
        "ttl_seconds": 3600,
        "module": "inventory"
    }
    await client.put("/api/v1/cache/inventory:clean:1", json=payload)

    response = await client.post("/api/v1/cache/cleanup")
    assert response.status_code == 200
    assert response.json()["cleaned_count"] >= 0

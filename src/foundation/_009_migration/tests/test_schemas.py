"""
Tests for Pydantic schemas.
"""
from datetime import datetime
from pydantic import ValidationError
import pytest

from src.foundation._009_migration.schemas import (
    MigrationModuleStatus,
    MigrationStatusResponse,
    MigrationApplyRequest,
    MigrationRollbackRequest,
    MigrationHistoryEntry
)

def test_migration_module_status():
    status = MigrationModuleStatus(
        module="_009_migration",
        current_version="abc",
        current_description="init",
        applied_count=1,
        last_applied_at=datetime.now()
    )
    assert status.module == "_009_migration"

    with pytest.raises(ValidationError):
        MigrationModuleStatus()

def test_migration_status_response():
    resp = MigrationStatusResponse(
        current_revision="abc",
        is_up_to_date=True,
        pending_count=0,
        modules=[]
    )
    assert resp.is_up_to_date is True

def test_migration_apply_request():
    req = MigrationApplyRequest(revision="123")
    assert req.revision == "123"
    assert req.applied_by == "system"

def test_migration_rollback_request():
    req = MigrationRollbackRequest(revision="123")
    assert req.revision == "123"
    assert req.rolled_back_by == "system"

    with pytest.raises(ValidationError):
        MigrationRollbackRequest()

def test_migration_history_entry():
    entry = MigrationHistoryEntry(
        id=1,
        version="abc",
        module="mod",
        description="desc",
        applied_at=datetime.now(),
        applied_by="system"
    )
    assert entry.id == 1
    assert entry.version == "abc"

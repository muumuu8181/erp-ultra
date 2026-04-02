from typing import Optional
from shared.types import BaseSchema


from pydantic import field_validator
from .validators import validate_attachment_code, validate_attachment_name

class AttachmentBase(BaseSchema):
    code: str
    name: str

    @field_validator('code')
    @classmethod
    def check_code(cls, v: str) -> str:
        if not validate_attachment_code(v):
            raise ValueError('code cannot be empty')
        return v

    @field_validator('name')
    @classmethod
    def check_name(cls, v: str) -> str:
        if not validate_attachment_name(v):
            raise ValueError('name cannot be empty')
        return v


class AttachmentCreate(AttachmentBase):
    pass


class AttachmentUpdate(BaseSchema):
    code: Optional[str] = None
    name: Optional[str] = None

    @field_validator('code')
    @classmethod
    def check_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not validate_attachment_code(v):
            raise ValueError('code cannot be empty')
        return v

    @field_validator('name')
    @classmethod
    def check_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not validate_attachment_name(v):
            raise ValueError('name cannot be empty')
        return v


class AttachmentResponse(AttachmentBase):
    id: int

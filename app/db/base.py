from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY


class CustomArray(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    metadata = MetaData()

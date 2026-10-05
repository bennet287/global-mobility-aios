"""Authenticated builder claims and bounded package manifests, without authority."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import Field, StrictInt, StrictStr, field_validator
from app.schemas_organization_rea_admission import Digest, StrictModel
from app.schemas_organization_rea_artifacts import Key, ReaArtifactScope


def package_path(value):
    if type(value) is not str or not value or len(value.encode('utf-8')) > 1024 or '\\' in value or '\x00' in value or any(ord(c) < 32 or ord(c) == 127 for c in value) or any(p in {'', '.', '..'} for p in value.split('/')):
        raise ValueError('package path must be canonical relative UTF-8')
    return value


class ReaPackageFile(StrictModel):
    path: StrictStr
    size: Annotated[StrictInt, Field(ge=0, le=16*1024*1024)]
    sha256: Digest
    _path = field_validator('path')(package_path)


class ReaBuildStatement(StrictModel):
    kind: Literal['rea_builder_statement_v1']
    source_commit: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{40}$')]
    source_materials_sha256: Digest
    catalog_sha256: Digest
    recipe_sha256: Digest
    dependency_lock_sha256: Digest
    package_name: Literal['rea-agents']
    package_version: Literal['3.2.1']
    builder_id: Key
    build_policy_sha256: Digest
    archive_sha256: Digest
    archive_bytes: Annotated[StrictInt, Field(ge=1, le=256*1024*1024)]
    files: Annotated[list[ReaPackageFile], Field(min_length=1, max_length=10000)]
    started_at: datetime
    finished_at: datetime

    @field_validator('builder_id')
    @classmethod
    def meaningful(cls, value):
        return ReaArtifactScope.meaningful(value)

    @field_validator('files', mode='before')
    @classmethod
    def explicit(cls, value):
        if type(value) is not list:
            raise ValueError('explicit files list required')
        return value

    @field_validator('files')
    @classmethod
    def complete(cls, value):
        paths = [v.path for v in value]
        if paths != sorted(paths) or len(set(paths)) != len(paths) or len({p.casefold() for p in paths}) != len(paths) or sum(v.size for v in value) > 256*1024*1024:
            raise ValueError('manifest must be sorted unique and bounded')
        return value

    @field_validator('started_at', 'finished_at', mode='before')
    @classmethod
    def explicit_time(cls, value):
        value = ReaArtifactScope.datetime_type(value)
        if type(value) is str:
            datetime.fromisoformat(value)
        return value

    @field_validator('started_at', 'finished_at')
    @classmethod
    def aware(cls, value):
        return ReaArtifactScope.aware(value)


class ReaSignedBuildStatement(StrictModel):
    statement: ReaBuildStatement
    signature_hex: Annotated[StrictStr, Field(pattern=r'^[0-9a-f]{128}$')]

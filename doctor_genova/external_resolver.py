from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class ExternalResolution(Protocol):
    def get_name(self) -> str:
        ...

    def get_url(self) -> str:
        ...

    def get_md_link(self) -> str:
        ...


@runtime_checkable
class ExternalResolver(Protocol):
    def resolve_name(self, name: str) -> None | ExternalResolution:
        ...

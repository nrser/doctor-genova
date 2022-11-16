from pathlib import Path
from typing import Callable, Iterable, Protocol, TypeVar

from novella.markdown.tagparser import (
    ReplacementFunc,
    replace_tags,
    parse_inline_tags,
    parse_block_tags,
)

T = TypeVar("T")


def index_where(iterable: Iterable[T], predicate: Callable[[T], bool]) -> int:
    for index, entry in enumerate(iterable):
        if predicate(entry):
            return index

    raise ValueError("no match")


def insert_before(
    list_: list[T], value: T, predicate: Callable[[T], bool]
) -> list[T]:
    """
    ##### Examples #####

    ```python
    >>> insert_before([1, 2, 3], 888, lambda n: n == 2)
    [1, 888, 2, 3]

    ```
    """
    list_.insert(index_where(list_, predicate), value)
    return list_


def get_default_search_path() -> list[str]:
    """Get the default list of paths to search for Python packages and modules.

    This behavior is coppied from

    [pydoc_markdown.novella.preprocessor.PydocTagPreprocessor](https://github.com/NiklasRosenstein/pydoc-markdown/blob/42fa47f91debba4ff7051ff58140fff8383245ac/src/pydoc_markdown/novella/preprocessor.py#L58)

    so that we find the same packages and modules by default.

    Basically:

    1.  If the current directory is named 'docs' or 'documentation', then
        the search path is

        ```python
        ["../src", ".."]
        ```

        (look in `src` in the parent directory, and the parent directory itself).

    2.  Otherwise it's

        ```python
        ["src", "."]
        ```

        (look in the `src` directory and this directory itself).

    """

    if Path.cwd().name.lower() in ("docs", "documentation"):
        return ["../src", ".."]
    else:
        return ["src", "."]


class HasContent(Protocol):
    content: str


def replace_inline_tags_in(
    target: HasContent, tag_name: str, replace: ReplacementFunc
) -> None:
    target.content = replace_tags(
        target.content,
        [t for t in parse_inline_tags(target.content) if t.name == tag_name],
        replace,
    )


def replace_block_tags_in(
    target: HasContent, tag_name: str, replace: ReplacementFunc
) -> None:
    target.content = replace_tags(
        target.content,
        [t for t in parse_block_tags(target.content) if t.name == tag_name],
        replace,
    )

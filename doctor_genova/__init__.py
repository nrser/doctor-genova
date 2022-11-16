from contextlib import contextmanager
from os import PathLike
from pathlib import Path
import logging
from collections.abc import Container
from typing import Generator, Iterable, Optional

import docspec_python
import yaml

from doctor_genova.api_page import APIPage
from doctor_genova.nav import ensure_child_nav, sort_nav

# Unused explicit imports that allow indirect linking.
from doctor_genova.backtick_preprocessor import BacktickPreprocessor


_LOG = logging.getLogger(__name__)

#: Default Mkdocs nav section to add generated pages to.
#:
#: ```python
#: "API Documentation"
#: ```
#:
DEFAULT_API_SECTION = "API Documentation"

#: Default package and module names to ignore when searching a _search path_.
#:
#: ```python
#: ("test", "tests", "setup")
#: ```
#:
DEFAULT_IGNORE_WHEN_DISCOVERED = ("test", "tests", "setup")


def generate_api_pages(
    build_dir: Path,
    search_path: Optional[Iterable[PathLike]] = None,
    ignore_when_discovered: Container[str] = DEFAULT_IGNORE_WHEN_DISCOVERED,
    nav_api_section: str = DEFAULT_API_SECTION,
) -> None:
    """Generate Markdown stub pages for each module found in the _search path_,
    if such a page does not already exist.

    ##### Stubs #####

    Generated stubs consist a title and `@pydoc` tag to include the module
    documentation.

    Stubs are written to:

        <build_dir>/content/<src_rel_dir>/<name>.md

    unless a directory exists named `<build_dir>/<src_rel_dir>/<name>`, in which
    case the path will be:

        <build_dir>/content/<src_rel_dir>/<name>/index.md

    For example, the `doctor_genova.api_page` module will have it's stub written
    to

        <build_dir>/content/doctor_genova/api_page.md

    ##### Mkdocs Nav Config #####

    If the file

        <build_dir>/mkdocs.yml

    exists then each stub that is generated will be added to the 'nav' (created
    if not found), under the `nav_api_section` section (also created if not
    found).

    ##### See Also #####

    1.  `doctor_genova.api_page.APIPage`

    """

    with mkdocs_api_nav(build_dir, nav_api_section) as api_nav:
        py_files = iter_py_files(
            search_path=search_path,
            ignore_when_discovered=ignore_when_discovered,
        )

        pages = [
            APIPage(module_rel_path, build_dir) for module_rel_path in py_files
        ]

        for page in pages:
            page.generate()
            page.add_to_api_nav(api_nav)


@contextmanager
def mkdocs_api_nav(
    build_dir: Path, api_section: str = DEFAULT_API_SECTION
) -> Generator[Optional[list], None, None]:
    """Context manager to edit the API documentation section of the 'nav' in
    a `mkdocs.yml` config file in the `build_dir`, _if one exists_.

    If the file _does_ exist:

    1.  It is read and parsed.

    2.  If it does not already have a 'nav' key, one is created containing and
        empty `list` (logs a warning).

    3.  We ensure that the 'nav' value has an entry called `api_header`,
        creating an empty list if needed.

    4.  That `api_header` entry is yielded as the context.

    5.  After control is returned, the `api_header` entry is recursively sorted
        via `sort_nav`.

    6.  The modified Mkdocs config is written back to `<build_dir>/mkdocs.yml`.

    If the file _does not_ exist:

    1.  A warning will be logged and `None` will be yielded as the context.

    """

    mkdocs_yml_path = build_dir / "mkdocs.yml"

    if not mkdocs_yml_path.exists():
        _LOG.warning("Mkdocs config not found at %s", mkdocs_yml_path)
        yield None
        return

    if not mkdocs_yml_path.is_file():
        _LOG.warning(
            "Mkdocs config found but not a file at %s", mkdocs_yml_path
        )
        yield None
        return

    mkdocs_config = yaml.safe_load(mkdocs_yml_path.open("r", encoding="utf-8"))

    _LOG.info("Loaded mkdocs config\n\n%s", yaml.safe_dump(mkdocs_config))

    if "nav" not in mkdocs_config:
        _LOG.warning("'nav' not found in Mkdocs config, adding")
        mkdocs_config["nav"] = []

    api_nav = ensure_child_nav(mkdocs_config["nav"], api_section)

    yield api_nav

    sort_nav(api_nav)

    yaml.safe_dump(mkdocs_config, mkdocs_yml_path.open("w", encoding="utf-8"))

    _LOG.info("Updated mkdocs config\n\n%s", yaml.safe_dump(mkdocs_config))


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


def iter_py_files(
    *,
    search_path: Optional[Iterable[PathLike[str]]] = None,
    ignore_when_discovered: Container[str] = DEFAULT_IGNORE_WHEN_DISCOVERED,
) -> Generator[Path, None, None]:
    """
    Yield `Path` to the individual Python source files that make up the packages
    and modules found in the `search_path` (see `get_default_search_path` for
    the default value).

    Paths are _relative_ to the `search_path` entry they are found under.
    """

    if search_path is None:
        search_path = get_default_search_path()

    for root_path in (Path(p).resolve() for p in search_path):
        try:
            discovered_items = list(docspec_python.discover(root_path))
        except FileNotFoundError:
            continue

        for item in discovered_items:
            if item.name not in ignore_when_discovered:
                if isinstance(item, docspec_python.DiscoveryResult.Module):
                    yield Path(item.filename).resolve().relative_to(root_path)

                elif isinstance(item, docspec_python.DiscoveryResult.Package):
                    package_root = Path(item.directory).resolve()
                    for py_path in package_root.glob("**/*.py"):
                        yield py_path.relative_to(root_path)

import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Optional
import io

from docspec import ApiObject, Indirection, Module
from novella.markdown.preprocessor import (
    MarkdownFile,
    MarkdownFiles,
    MarkdownPreprocessor,
)
from novella.markdown.tagparser import Tag
from pydoc_markdown.contrib.loaders.python import PythonLoader
from pydoc_markdown.contrib.processors.crossref import CrossrefProcessor
from pydoc_markdown.contrib.processors.filter import FilterProcessor
from pydoc_markdown.contrib.processors.smart import SmartProcessor
from pydoc_markdown.contrib.renderers.markdown import (
    MarkdownReferenceResolver,
    MarkdownRenderer,
)
from pydoc_markdown.interfaces import (
    Context,
    Loader,
    Processor,
    SingleObjectRenderer,
)
from pydoc_markdown.novella.preprocessor import autodetect_source_linker
from pydoc_markdown.util.docspec import ApiSuite

from .docstring_backtick_processor import DocstringBacktickProcessor
from .lib import (
    get_default_search_path,
    replace_block_tags_in,
    replace_inline_tags_in,
)
from .stdlib_resolver import StdlibResolver

_LOG = logging.getLogger(__name__)


class DrGenPreprocessor(MarkdownPreprocessor):
    """Replaces simple backtick spans with links when they seem to point to:

    1.  Another object in the documented package.
    2.  An object in the Python standard library.

    """

    _loader: Loader
    _processors: list[Processor]
    _renderer: SingleObjectRenderer
    _stdlib_resolver: StdlibResolver | None = None

    def __post_init__(self) -> None:
        self._loader = PythonLoader(search_path=get_default_search_path())

        resolver_v2 = MarkdownReferenceResolver(global_=True)
        self._stdlib_resolver = StdlibResolver()

        self._processors = [
            FilterProcessor(),
            SmartProcessor(),
            # We return the entire link formatted as a Novella {@link} tag in #resolve_ref().
            CrossrefProcessor(resolver_v2=resolver_v2),
            DocstringBacktickProcessor(
                resolver_v2=resolver_v2,
                stdlib_resolver=self._stdlib_resolver,
            ),
        ]

        self._renderer = MarkdownRenderer(
            source_linker=autodetect_source_linker(),
            render_novella_anchors=True,
            render_module_header=False,
            descriptive_class_title="Class ",
        )

    @cached_property
    def context(self) -> Context:
        return Context(str(Path.cwd()))

    @cached_property
    def loader(self) -> Loader:
        self._loader.init(self.context)
        return self._loader

    @cached_property
    def renderer(self) -> MarkdownRenderer:
        self._renderer.init(self.context)
        return self._renderer

    @cached_property
    def publication_modules(self) -> list[Module]:
        modules = list(self.loader.load())
        for processor in self._processors:
            processor.process(modules, self)
        return modules

    @cached_property
    def publication_suite(self) -> ApiSuite:
        return ApiSuite(self.publication_modules)

    @cached_property
    def resolution_suite(self) -> ApiSuite:
        return ApiSuite(list(self.loader.load()))

    def setup(self) -> None:
        if self.dependencies is None and self.predecessors is None:
            self.precedes("anchor")

    def process_files(self, files: MarkdownFiles) -> None:
        for file in files:
            replace_block_tags_in(
                file,
                "pydoc",
                lambda tag: self._replace_pydoc_tag(file, tag),
            )

            replace_inline_tags_in(file, "pylink", self._replace_pylink_tag)

            self._replace_backticks(file)

    def _replace_backticks(self, file: MarkdownFile) -> None:
        file.content = DocstringBacktickProcessor.BACKTICK_RE.sub(
            self._replace_backticks_handler,
            file.content,
        )

    def _resolve_api_object(self, name: str) -> Optional[ApiObject]:
        api_objects = self.resolution_suite.resolve_fqn(name)

        count = len(api_objects)

        if count == 0:
            return None

        if count > 1:
            _LOG.warning(
                "  found multiple ApiObject for name <fg=cyan>%s</fg>\n\n%s",
                name,
                "\n".join(repr(api_object) for api_object in api_objects),
            )

        return api_objects[0]

    def _resolve_link(self, name: str) -> Optional[str]:
        if api_object := self._resolve_api_object(name):
            if isinstance(api_object, Indirection):
                _LOG.info(
                    "  <fg=yellow>INDIRECTION</fg> <fg=cyan>%s</fg> -> <fg=yellow>%s</fg>",
                    name,
                    api_object.target,
                )
                return self._resolve_link(api_object.target)

            else:
                link = "{{@link pydoc:{}}}".format(
                    ".".join(x.name for x in api_object.path)
                )

                _LOG.info(
                    "  <fg=green>TAG</fg> <fg=cyan>%s</fg> -> <fg=green>%s</fg>",
                    name,
                    link,
                )

                return link

        else:
            if resolution := self._stdlib_resolver.resolve_name(name):
                _LOG.info(
                    "  <fg=magenta>STDLIB</fg> <fg=cyan>%s</fg> -> <fg=magenta>%s</fg>",
                    name,
                    resolution.md_link,
                )
                return resolution.md_link

            else:
                _LOG.info("  <fg=red>NO MATCH</fg>")
                return None

    def _replace_backticks_handler(self, match: re.Match) -> str:
        src = match.group(0)
        fqn = match.group(1)

        _LOG.info("processing MD backtick <fg=cyan>%s</fg>", src)

        if link := self._resolve_link(fqn):
            return link
        else:
            return src

    def _replace_pydoc_tag(self, file: MarkdownFile, tag: Tag) -> str | None:
        fqn = tag.args.strip()

        objects = self.publication_suite.resolve_fqn(fqn)
        if len(objects) > 1:
            _LOG.warning(
                "  found multiple matches for Python FQN <fg=cyan>%s</fg>", fqn
            )
        elif not objects:
            _LOG.warning(
                "  found no match for Python FQN <fg=cyan>%s</fg>", fqn
            )
            return None

        fp = io.StringIO()
        self.renderer.render_object(fp, objects[0], tag.options)
        return self.action.repeat(file.path, file.output_path, fp.getvalue())

    def _replace_pylink_tag(self, tag: Tag) -> str | None:
        """
        Override `PydocTagPreprocessor._replace_pylink_tag` to check if the
        link content is a Python stdlib path, and use that if so.

        This is not ideal, because it actually allows stdlib to shaddow the
        package in case of conflict, which is probably backwards of what you
        would expect, but it's simple as an initial version.
        """
        name = tag.args.strip()

        _LOG.info("processing @pylink tag <fg=cyan>%s</fg>", name)

        if link := self._resolve_link(name):
            return link

        return f"`{name}`"

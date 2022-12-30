from collections import defaultdict
import logging
import re
from functools import cached_property, partial
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
from novella.build import BuildContext

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
    Resolver,
    ResolverV2,
)
from pydoc_markdown.novella.preprocessor import autodetect_source_linker
from pydoc_markdown.util.docspec import ApiSuite

from .docstring_backtick_processor import DocstringBacktickProcessor
from .lib import (
    get_default_search_path,
    is_subpath,
    replace_block_tags_in,
    replace_inline_tags_in,
)
from .stdlib_resolver import StdlibResolver

_LOG = logging.getLogger(__name__)


class DrGenPreprocessor(MarkdownPreprocessor, Resolver):
    """Replaces simple backtick spans with links when they seem to point to:

    1.  Another object in the documented package.
    2.  An object in the Python standard library.

    """

    _loader: Loader
    _processors: list[Processor]
    _renderer: MarkdownRenderer
    _stdlib_resolver: StdlibResolver
    _publication_suite: Optional[ApiSuite] = None
    _resolution_suite: Optional[ApiSuite] = None
    _scope_api_objects: dict[Path, dict[str, ApiObject]]
    _resolver_v2: ResolverV2

    def __post_init__(self) -> None:
        self._scope_api_objects = defaultdict(dict)

        self._loader = PythonLoader(search_path=get_default_search_path())

        self._resolver_v2 = MarkdownReferenceResolver(global_=True)
        self._stdlib_resolver = StdlibResolver()

        self._processors = [
            FilterProcessor(),
            SmartProcessor(),
            # We return the entire link formatted as a Novella {@link} tag in #resolve_ref().
            CrossrefProcessor(resolver_v2=self._resolver_v2),
            DocstringBacktickProcessor(
                resolver_v2=self._resolver_v2,
                stdlib_resolver=self._stdlib_resolver,
            ),
        ]

        self._renderer = MarkdownRenderer(
            source_linker=autodetect_source_linker(),
            render_novella_anchors=True,
            render_module_header=False,
            descriptive_class_title=False,
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

    @property
    def resolution_suite(self) -> ApiSuite:
        if self._resolution_suite is None:
            raise AttributeError(
                "`resolution_suite` not available; run `process_modules` first"
            )
        return self._resolution_suite

    @property
    def publication_suite(self) -> ApiSuite:
        if self._publication_suite is None:
            raise AttributeError(
                "`publication_suite` not available; run `process_modules` first"
            )
        return self._publication_suite

    def process_modules(self, build: BuildContext):
        """Process the package modules (Python files). Execution sets the
        `publication_suite` and `resolution_suite` properties, overwriting
        them if they are already set (which is important for re-running).

        A few important things to note:

        1.  Processing the modules also _filters_ the list, which in turn
            filters what is available in the `publication_suite` that ends up
            included in the docs.

            This needs to be redone when the action is rerun because the changes
            triggering the rerun may change what api objects are included in the
            publication suite.

            An example of this is a change that adds documentation to an api
            objects that did not have any — on the previous run it would have
            been filtered out, but on the rerun it needs to be included.

        2.  This filtering is why we have a separate `resolution_suite` to
            resolve links against. In particular, the filtering removes the
            indirection nodes that make indirect linking possible.

            This also needs to be reloaded on rerun because new api objects
            could be introduced.
        """
        # WARNING   Needs to be _before_ the processing loop!
        #
        # WARNING   Not sure why, but this needs to be a separate load from the
        #           loader; loading once and copying the list doesn't work for
        #           whatever reason I haven't looked into.
        self._resolution_suite = ApiSuite(list(self.loader.load()))

        # Load a list
        modules = list(self.loader.load())

        # Figure out what directories to watch

        # Get a set of all source files from the `Module` that were loaded
        module_dirs = {
            Path(module.location.filename).resolve().parent
            for module in modules
        }

        # The directories we want to watch are the roots — those which are _not_
        # subpaths of any of the _other_ ones.
        watch_dirs = [
            watch_dir
            for watch_dir in module_dirs
            if not any(
                is_subpath(watch_dir, module_dir)
                for module_dir in module_dirs
                if module_dir != watch_dir
            )
        ]

        # Tell the build context to watch those directories too! It keeps a set
        # if watched paths that it checks before adding, so this is idempotent.
        for watch_dir in watch_dirs:
            build.watch(watch_dir)

        # Process the modules and set the suite

        for processor in self._processors:
            processor.process(modules, self)

        self._publication_suite = ApiSuite(modules)

    def resolve_ref(self, scope: ApiObject, ref: str) -> None | str:
        return self._resolve_link(None, ref)

    def setup(self) -> None:
        if self.dependencies is None and self.predecessors is None:
            self.precedes("anchor")

    def process_files(self, files: MarkdownFiles) -> None:
        self.process_modules(files.build)

        for file in files:
            replace_block_tags_in(
                file,
                "pydoc",
                lambda tag: self._replace_pydoc_tag(file, tag),
            )

            replace_block_tags_in(
                file, "pyscope", partial(self._replace_pyscope_tag, file)
            )

            replace_inline_tags_in(
                file,
                "pylink",
                partial(self._replace_pylink_tag, file),
            )

            self._replace_backticks(file)

    def _replace_backticks(self, file: MarkdownFile) -> None:
        file.content = DocstringBacktickProcessor.BACKTICK_RE.sub(
            partial(self._replace_backticks_handler, file),
            file.content,
        )

    def _resolve_api_object(
        self, file: None | MarkdownFile, name: str
    ) -> None | ApiObject:
        api_objects = self.resolution_suite.resolve_fqn(name)

        count = len(api_objects)

        if count == 0 and file is not None:
            for node in self._scope_api_objects[file.path.absolute()].values():
                _LOG.info("resolving %s against reference %s", name, node.name)

                if (
                    api_object := self._resolver_v2.resolve_reference(
                        self.resolution_suite, node, name
                    )
                ) and api_object.parent is node:
                    api_objects.append(api_object)

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

    def _resolve_link(self, file: None | MarkdownFile, name: str) -> None | str:
        if api_object := self._resolve_api_object(file, name):
            if isinstance(api_object, Indirection):
                _LOG.info(
                    "  <fg=yellow>INDIRECTION</fg> <fg=cyan>%s</fg> -> <fg=yellow>%s</fg>",
                    name,
                    api_object.target,
                )
                return self._resolve_link(file, api_object.target)

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

    def _replace_backticks_handler(
        self, file: MarkdownFile, match: re.Match
    ) -> str:
        src = match.group(0)
        fqn = match.group(1)

        _LOG.info("processing MD backtick <fg=cyan>%s</fg>", src)

        if link := self._resolve_link(file, fqn):
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

    def _replace_pylink_tag(self, file: MarkdownFile, tag: Tag) -> str | None:
        name = tag.args.strip()

        _LOG.info("processing @pylink tag <fg=cyan>%s</fg>", name)

        if link := self._resolve_link(file, name):
            return link

        return f"`{name}`"

    def _replace_pyscope_tag(self, file: MarkdownFile, tag: Tag) -> str:
        name = tag.args.strip()

        _LOG.info("processing @pyscope tag <fg=cyan>%s</fg>", name)

        api_objects = self.resolution_suite.resolve_fqn(name)

        if len(api_objects) == 0:
            _LOG.warning(
                "found no api objects for @pyscope tag <fg=cyan>%s</fg>", name
            )
        else:
            _LOG.info(
                "adding reference api objects for @pyscope tag <fg=cyan>%s</fg>: %s",
                name,
                ", ".join(
                    f"{obj.__class__.__name__}:{obj.name}"
                    for obj in api_objects
                ),
            )

        for api_object in api_objects:
            self._scope_api_objects[file.path.absolute()][
                api_object.name
            ] = api_object

        # Replace the tag with nothing
        return ""

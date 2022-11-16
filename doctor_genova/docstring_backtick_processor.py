from dataclasses import dataclass
import logging
from pathlib import Path
import re
from typing import Optional
from doctor_genova.lib import replace_inline_tags_in

from pydoc_markdown.util.docspec import ApiSuite
from pydoc_markdown.interfaces import Processor, Resolver, ResolverV2
from docspec import ApiObject, Module, visit
from novella.markdown.tagparser import (
    Tag,
    parse_block_tags,
    parse_inline_tags,
    replace_tags,
)

from .stdlib_resolver import StdlibResolver

_LOG = logging.getLogger(__name__)


@dataclass
class DocstringBacktickProcessor(Processor):
    BACKTICK_RE = re.compile(
        r"\B`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`"
    )

    resolver_v2: ResolverV2
    stdlib_resolver: StdlibResolver

    def process(
        self, modules: list[Module], resolver: Optional[Resolver]
    ) -> None:
        visit(
            modules,
            lambda x: self._preprocess_refs(x, ApiSuite(modules), resolver),
        )

    def _preprocess_refs(
        self,
        node: ApiObject,
        suite: ApiSuite,
        resolver: Optional[Resolver],
    ) -> None:
        if not node.docstring:
            return

        node.docstring.content = self.BACKTICK_RE.sub(
            lambda match: self._replace_match(node, suite, resolver, match),
            node.docstring.content,
        )

        replace_inline_tags_in(
            node.docstring,
            "pylink",
            lambda tag: self._replace_pylink_tag(node, suite, resolver, tag),
        )

    def _resolve_link(
        self,
        node: ApiObject,
        suite: ApiSuite,
        resolver: Optional[Resolver],
        name: str,
    ):
        if api_object := self.resolver_v2.resolve_reference(suite, node, name):
            link = "{{@link pydoc:{}}}".format(
                ".".join(x.name for x in api_object.path)
            )

            _LOG.info(
                "  <fg=green>NODE TAG</fg> <fg=cyan>%s</fg> -> <fg=green>%s</fg>",
                name,
                link,
            )

            return link

        if link := resolver._resolve_link(name):
            return link

        return None

    def _replace_match(
        self,
        node: ApiObject,
        suite: ApiSuite,
        resolver: Optional[Resolver],
        match: re.Match,
    ):
        src = match.group(0)
        name = match.group(1)

        if link := self._resolve_link(node, suite, resolver, name):
            return link

        _LOG.info(
            "  <fg=red>SRC</fg> <fg=cyan>%s</fg> -> <fg=red>%s</fg>",
            name,
            src,
        )
        return src

    def _replace_pylink_tag(
        self,
        node: ApiObject,
        suite: ApiSuite,
        resolver: Optional[Resolver],
        tag: Tag,
    ):
        return self._resolve_link(node, suite, resolver, tag.args.strip())

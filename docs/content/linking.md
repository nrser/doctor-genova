Linking
==============================================================================

Dr. Genova augments the auto-linking capabilities of [pydoc-markdown][] and
[novella][] in two ways:

1.  **Backtick Linking** — _backtick spans_ (delimited with &#96;) are linked if
    they can be resolved, in both source (python) and documentation (markdown)
    files.
    
2.  **Stdlib Linking** — resolution is attempted against the Python standard 
    library, linking to the online docs.

[pydoc-markdown]: https://pypi.org/project/pydoc-markdown/
[novella]: https://pypi.org/project/novella/

> 📝 NOTE
> 
> Much things break after auto-update refresh when running `novella` in
> `--serve` mode, noted with the yellow dot 🟡 below.
> 
> Looks like the problem is in 
> 
> [novella.markdown.tags.anchor.AnchorTagProcessor](https://github.com/NiklasRosenstein/novella/blob/6d80d06e6688306aa7628385cdeae103a7cf62f3/src/novella/markdown/tags/anchor.py#L57)
> 
> Right now, it clears the map of anchors on re-run, but those anchors are not
> recreated, so it can't find them.

Documentation File (Markdown) Linking Tests
------------------------------------------------------------------------------

We are in a **_docs file_** (`docs/content/**/*.md`) here, specifically
`docs/content/linking.md`.

> 📝 NOTE
> 
> As we are in a Markdown file, there is no source node to resolve local
> references against. Hence the type _Local_ rows are omitted from the following
> tables, though they are present further down in the _Module Documentation_
> section.

### Hash Prefix ###

| Status |   Type   |                      Source                       |   Render   |
| ------ | -------- | ------------------------------------------------- | ---------- |
| 🔴¹     | FQN      | &#35;doctor_genova.preprocessor.DrGenPreprocessor | (omitted)² |
| 🔴¹     | Stdlib   | &#35;typing.IO                                    | (omitted)² |
| 🔴¹     | Indirect | &#35;doctor_genova.DrGenPreprocessor              | (omitted)² |

> ¹ Does not seem that Hash Prefix links are indended to be supported in
> Markdown files.
> 
> ² Attempting to render results in `h1` tags that clutter up the display, so
> they have been omitted.

### `@pylink` Tag ###

| Status |   Type   |                           Source                            |                         Render                         |
| ------ | -------- | ----------------------------------------------------------- | ------------------------------------------------------ |
| 🟢      | FQN      | &#123;@pylink doctor_genova.preprocessor.DrGenPreprocessor} | {@pylink doctor_genova.preprocessor.DrGenPreprocessor} |
| 🟢      | Stdlib   | &#123;@pylink typing.IO}                                    | {@pylink typing.IO}                                    |
| 🟠³     | Indirect | &#123;@pylink doctor_genova.DrGenPreprocessor}              | {@pylink doctor_genova.DrGenPreprocessor}              |

> ³ Fails on initial render, then succeeds on dynamic re-render (sometimes?).

### Backtick Span ###

| Status |   Type   |                         Source                         |                     Render                     |
| ------ | -------- | ------------------------------------------------------ | ---------------------------------------------- |
| 🟡⁴     | FQN      | &#96;doctor_genova.preprocessor.DrGenPreprocessor&#96; | `doctor_genova.preprocessor.DrGenPreprocessor` |
| 🟢      | Stdlib   | &#96;typing.IO&#96;                                    | `typing.IO`                                    |
| 🟡⁴     | Indirect | &#96;doctor_genova.DrGenPreprocessor&#96;              | `doctor_genova.DrGenPreprocessor`              |

> ⁴ Succeeds on initial render, then fails on dynamic re-render.

Source File (Python) Linking Tests
------------------------------------------------------------------------------

Included via `@pydoc <MODULE_NAME>` tag, where

    MODULE_NAME=doctor_genova._linking

***

@pydoc doctor_genova._linking

***

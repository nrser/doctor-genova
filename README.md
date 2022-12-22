Dr. Genova, MD
==============================================================================

Generate and link API docs from Markdown, both in Python docstrings and separate
Markdown files, using [Nikky Rosenstein's][NiklasRosenstein] ensemble of
[pydoc-markdown][] / [novella][] / [docspec][].

[NiklasRosenstein]: https://github.com/NiklasRosenstein
[pydoc-markdown]: https://niklasrosenstein.github.io/pydoc-markdown/
[novella]: https://niklasrosenstein.github.io/novella/
[docspec]: https://niklasrosenstein.github.io/docspec/

Motivation
------------------------------------------------------------------------------

Writing Python doc in Markdown, like we do everywhere else. Instead of the wonky
ReStructured Text thing that I can never seem to remember.

Every other Python/Markdown doc gen approach I've tried has been a worse
experience, and I feel like I've tried quite a few. Thanks
[Nikky][NiklasRosenstein]!

Features
------------------------------------------------------------------------------

1.  Generating an API documentation page for each module.
2.  Mix-and-match generated and hand-written docs.
3.  Automatic linking of simple backtick-delimited spans.
4.  Automatic linking to the Python standard library online docs.

Problems
------------------------------------------------------------------------------

1.  Hella stuff doesn't work correctly or consistently. At least some of this
    seems to be in [pydoc-markdown][] and/or [Novella][], which makes sense as
    the later is super new and unstable (as of 2022-11-15).
    
2.  Code kinda sucks. It's a bit slap-n-dash, honestly... just wanted to get
    docs rendering reasonably so I understood the rendering I was writing
    against.
    
3.  I'm using the [mkdocs-material][] theme only. I know a lot of people use
    that "read the docs" thing, but I haven't fucked w that, so I don't know
    how it will (or won't) go.

[mkdocs-material]: https://pypi.org/project/mkdocs-material/

Config
------------------------------------------------------------------------------

See `docs/novella.build` and `docs/mkdocs.yml` for the latest example.

Some basic advices:

1.  Put your docs in a directory called `docs`. Other things may be possible,
    but this is easiest from my experience.
    
2.  Put your hand-written docs in `docs/content`.

3.  Add all the hand-written docs to the 'nav' in `docs/mkdocs.yml`.

Execution
------------------------------------------------------------------------------

To generate docs, from the package root:

    poetry run novella --directory ./docs

or to serve locally:

    poetry run novella --directory ./docs --serve

If you'd like to set the bind address and port, do it like:

    poetry run novella --directory ./docs --serve --dev-addr 127.0.0.1:8765

You can't just tack on Mkdocs options to the `novella` command; the `--dev-addr`
option was explicitly added via `doctor_genova.templates.DrGenMkdocsTemplate`.

That's where to look if you need to add more of 'em, and it can be subclassed to
do so. You will need to also add an additional _entry point_ in your
`pyproject.toml` or `setup.py` file that looks something like

```toml
[tool.poetry.plugins."novella.templates"]
my_mkdocs = "my_package.templates:MyMkdocsTemplate"
```

and get the build / install to trigger (`poetry install` or some such).

### Watch & Serve Alternative Method ###

> When I was starting out with this package I couldn't get `--serve` to
> auto-update reasonably. I think a lot of that has been solved, but I'm going
> to leaving this alternative approach in here for the moment.

Another option to "watch" and re-build:

1.  Install [entr](https://eradman.com/entrproject/).

2.  Have `entr` watch the files and run the `novella` command:
    
    ```shell
    ls doctor_genova/**/*.py docs/content/**/*.md docs/build.novella docs/mkdocs.yml | entr poetry run novella -d ./docs
    ```
    
3.  In another terminal, serve the files:
    
    ```shell
    python -m http.server 8080 --bind 127.0.0.1 --directory docs/_site/
    ```

License
------------------------------------------------------------------------------

BSDx3, holdin' it down for the bay.

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

The local server thing tries to watch and auto-update/refresh, but it doesn't
seem to watch everything, and a lot of stuff doesn't update or breaks when it
does decide to refresh.

License
------------------------------------------------------------------------------

BSDx3, holdin' it down for the bay.

"""cartoonomics — aggregate, analyze, and cartoonize Indian financial data.

This package implements the foundational data pipeline described in
``requirements.md`` (the single source of truth):

    scrape/ingest (§7.1) -> parse documents (§7.1 FR-1.5)
    -> analyze/normalize (§7.2) -> emit the predefined "CartoonSpec" format (§7.6)

The frontend renderer consumes the CartoonSpec to draw the animated cartoons.
"""

__version__ = "0.1.0"

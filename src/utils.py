"""Shared logging utilities for the MP2 REST API."""

import logging


def setup_logging(verbose=False):
    """Configure INFO logging, or DEBUG logging when verbose is enabled."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

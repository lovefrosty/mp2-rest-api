"""Shared logging and input-path helpers for the pipeline."""

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    """Configure INFO logging, or DEBUG logging when verbose is enabled."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


def validate_input(filepath):
    """Log whether a required input path exists and points to a file."""
    if not Path(filepath).is_file():
        logger.error("Input file not found: %s", filepath)
        return False

    logger.info("Input file validated: %s", filepath)
    return True

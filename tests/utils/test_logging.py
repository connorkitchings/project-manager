"""Tests for the logging utility."""

import logging

from project_manager.utils.logging import get_logger, logger, setup_logging


def test_logger_name():
    assert logger.name == "project_manager"


def test_setup_logging_sets_root_level(tmp_path):
    log_file = tmp_path / "app.log"
    setup_logging(level="INFO", log_file=log_file)

    named_logger = get_logger("project_manager.test")
    named_logger.info("hello")

    assert logging.getLogger().level == logging.INFO
    assert log_file.exists()

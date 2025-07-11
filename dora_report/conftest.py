import pytest
import logging

@pytest.fixture(scope="session")
def root_logger(caplog):
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger(logname).setLevel(logging.DEBUG)
    return logger
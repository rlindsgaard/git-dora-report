import pytest
import logging

@pytest.fixture(scope="session")
def root_logger():
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("dora_report.test")
    logger.setLevel(logging.DEBUG)
    return logger
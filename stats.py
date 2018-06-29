from config import PROVIDERS
from database import dbopen
from logzero import logger

with dbopen() as cur:
    query = """
    SELECT count(*) from progress
    WHERE progress = 1;
    """
    cur.execute(query)
    logger.info(f"total coordinates searched: {cur.fetchone()}")
    for provider in PROVIDERS:
        query = f"""
        SELECT count(*) from {provider};
        """
        cur.execute(query)
        logger.info(f"{provider}: {cur.fetchone()}")

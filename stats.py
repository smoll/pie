from config import PROVIDERS
from database import dbopen
from logzero import logger

name_mapping = {
    'uber_eats': 'payload_storePayload_stateMapDisplayInfo_available_title_text'
}

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

    for provider in PROVIDERS:
        name_column = name_mapping.get(provider, 'name')
        query = f"""
        SELECT {name_column}, count({name_column}) as count
        FROM {provider}
        GROUP BY {name_column}
        ORDER BY count DESC;
        """
        cur.execute(query)
        logger.info(f"{provider} top 20 restaurant name counts:")
        for name, count in cur.fetchall()[:20]:
            print(f"{name}={count}")

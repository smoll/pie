# Pre-process input csv files

from logzero import logger
from pathlib import Path
import glob
import pandas as pd
import pandas.api.types as ptypes

if __package__ is None:
    import sys
    from os import path
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    from database import dbopen, setup
    from config import PROVIDERS
else:
    from ..database import dbopen, setup
    from ..config import PROVIDERS

# Make outputs dir
Path('./outputs').mkdir(parents=True, exist_ok=True)

# Output *.csv files
with dbopen(return_conn=True) as conn:
    for provider in PROVIDERS:
        df = pd.read_sql(f"SELECT * FROM {provider};", conn)
        df.to_csv(f"./outputs/{provider}.csv", index=False)

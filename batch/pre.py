# Pre-process input csv files

from logzero import logger
from pathlib import Path
import pandas as pd
import pandas.api.types as ptypes

# Make outputs dir
Path('./outputs').mkdir(parents=True, exist_ok=True)

# From https://gist.github.com/erichurst/7882666
df_zips = pd.read_csv('./inputs/zip_coords.csv')
df_zips.rename(columns=lambda x: x.lower(), inplace=True)
df = None

pathlist = Path('./csvs').glob('**/*.csv')
for path in pathlist:
    # because path is object not string
    path_str = str(path)
    logger.info('loading %s...' % path_str)
    df_cbsa = pd.read_csv(path_str)
    df_cbsa.columns = ['idx', 'cbsa', 'zip_code']
    err = f"zip_code column (column #3) is not numeric for file: {path_str}"
    assert ptypes.is_numeric_dtype(df_cbsa['zip_code']), err

    combined_data = pd.merge(df_cbsa, df_zips, left_on='zip_code', right_on='zip')[['lat', 'lng']]
    df = combined_data if df is None else df.append(combined_data)

    assert df.isnull().values.any() == False, "Sanity check failed: one or more zip codes could not be mapped to a (lat, lng)"

    logger.info('running total # of coords: %s' % (df.shape,))

df['progress'] = 0

logger.info('head:\n%s' % (df.head(),))
logger.info('types:\n%s' % (df.dtypes,))

df.to_csv('./outputs/progress.csv')

# import pdb; pdb.set_trace()

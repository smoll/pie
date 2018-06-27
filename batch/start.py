# Start batch processing, storing progress in outputs/progress.csv

from logzero import logger
import pandas as pd

def main():
    df = pd.read_csv('./outputs/progress.csv')
    df = df.head(2) # DEBUG ONLY!!!



if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
        from crawler import CrawlWorker
        from config import PROVIDERS
    else:
        from ..crawler import CrawlWorker
        from ..config import PROVIDERS

    main()

import pandas as pd
from config import *
from utils.fmp_client import FmpClient
from utils.log_utils import *
import time
from utils.df_utils import cap_outliers
from utils.file_utils import *


class FmpGrowthLoader:
    def __init__(self, fmp_api_key):
        self.fmp_client = FmpClient(fmp_api_key)

    def calculate_growth_factor(self, symbol, growth_df):
        if growth_df is None or len(growth_df) == 0:
            logw(f"Not enough income growth data for {symbol}")
            return 0

        revenue_growth = growth_df['growthRevenue'].iloc[0]  # Get most recent value
        net_income_growth = growth_df['growthNetIncome'].iloc[0]

        # Weighted factor calculation
        growth_factor = 0.66 * revenue_growth + 0.33 * net_income_growth
        return growth_factor

    def fetch(self, symbol_list):
        i = 1
        growth_results_df = pd.DataFrame()
        for symbol in symbol_list:
            logd(f"Fetching growth for {symbol}... ({i}/{len(symbol_list)})")

            # Fetch quarterly growth
            quarterly_growth_df = self.fmp_client.get_income_growth(symbol, period="quarterly")
            store_csv(CACHE_DIR, f"{symbol}_quarterly_growth.csv", quarterly_growth_df)

            # Calculate growth factor
            quarterly_growth_factor = self.calculate_growth_factor(symbol, quarterly_growth_df)

            # Fetch annual growth
            annual_growth_df = self.fmp_client.get_income_growth(symbol, period="annual")
            store_csv(CACHE_DIR, f"{symbol}_annual_growth.csv", annual_growth_df)

            # Calculate annual growth factor
            annual_growth_factor = self.calculate_growth_factor(symbol, annual_growth_df)

            # Combine annual and quarterly growth
            growth_factor = 0.6 * quarterly_growth_factor + 0.4 + annual_growth_factor

            row = pd.DataFrame({'symbol': [symbol], 'growth_factor': [growth_factor]})
            growth_results_df = pd.concat([growth_results_df, row], axis=0, ignore_index=True)

            i += 1

            # Throttle for API limit
            time.sleep(API_REQUEST_DELAY)

        # Cap outliers in the growth factor results
        growth_results_df = cap_outliers(growth_results_df, 'growth_factor')

        return growth_results_df

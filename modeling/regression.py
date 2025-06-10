from src.commonconst import *

def extract_time_series(df_row, value_type):
    """
    Extracts funding data from 2016–2024 for a single funding variable.
    Fills NaNs with 0s to allow modeling even when partial data exists.
    """
    data = []
    for year in TRAIN_YEARS:
        col = f"{year} {value_type}"
        val = df_row[col] if col in df_row else 0
        data.append((year, val if pd.notna(val) else 0))
    return pd.DataFrame(data, columns=["Year", value_type])


def train_predict_series(df_series, value_type):
    """
    Trains an XGBoost model on the time series and predicts the next year's value.
    Returns None if all historical values are 0 or training fails.
    """
    if df_series.empty or df_series[value_type].sum() == 0:
        return None

    try:
        X = df_series[["Year"]]
        y = df_series[value_type]

        model = XGBRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        next_year = pd.DataFrame({"Year": [FORECAST_YEAR]})
        next_year[value_type] = model.predict(next_year)

        return next_year
    except Exception:
        return None


def predict_funding_for_country(df_country):
    """
    For a given single-country row (as a 1-row DataFrame),
    return a DataFrame with 2026 predictions or an explanatory string if modeling fails.
    """
    row = df_country.iloc[0]

    forecasts = []
    for var in FUNDING_VARS:
        ts = extract_time_series(row, var)
        forecast = train_predict_series(ts, var)
        if forecast is None:
            return "Due to shortage of funding reporting, we can't use the model to make such prediction."
        forecasts.append(forecast)

    # Merge forecasts on 'Year'
    final = forecasts[0]
    for df in forecasts[1:]:
        final = final.merge(df, on="Year", how="outer")

    return final.round(2)
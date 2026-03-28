import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load datasets (update file paths)
trades = pd.read_csv("historical_data.csv")
sentiment = pd.read_csv("fear_greed_index.csv")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
	"""Normalize headers for safer matching across CSV exports."""
	df = df.copy()
	df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
	return df


trades = normalize_columns(trades)
sentiment = normalize_columns(sentiment)

# Map commonly seen alternative headers to the names used by analysis.
if "timestamp_ist" in trades.columns:
	trades["time"] = trades["timestamp_ist"]
elif "timestamp" in trades.columns:
	trades["time"] = trades["timestamp"]

if "closed_pnl" in trades.columns and "closedpnl" not in trades.columns:
	trades = trades.rename(columns={"closed_pnl": "closedpnl"})

sentiment = sentiment.rename(
	columns={
		"date": "date",
		"classification": "classification",
	}
)

# ---------------------------
# Data Cleaning
# ---------------------------
required_trade_cols = {"time", "closedpnl", "side"}
required_sentiment_cols = {"date", "classification"}

missing_trade_cols = required_trade_cols - set(trades.columns)
missing_sentiment_cols = required_sentiment_cols - set(sentiment.columns)

if missing_trade_cols:
	raise KeyError(f"Missing required trade columns: {sorted(missing_trade_cols)}")
if missing_sentiment_cols:
	raise KeyError(f"Missing required sentiment columns: {sorted(missing_sentiment_cols)}")

trades['time'] = pd.to_datetime(trades['time'], dayfirst=True, errors='coerce')
sentiment['date'] = pd.to_datetime(sentiment['date'], errors='coerce')

# Remove rows with invalid timestamps before date extraction.
trades = trades.dropna(subset=['time'])
sentiment = sentiment.dropna(subset=['date'])

# Extract date for merging
trades['date'] = trades['time'].dt.date
sentiment['date'] = sentiment['date'].dt.date

# Merge datasets
df = pd.merge(trades, sentiment, on='date', how='left')

# Drop missing sentiment rows
df = df.dropna(subset=['classification'])

# ---------------------------
# Feature Engineering
# ---------------------------
df['PnL'] = pd.to_numeric(df['closedpnl'], errors='coerce')

# Convert side to numeric
df['side'] = df['side'].astype(str).str.upper().map({'BUY': 1, 'SELL': -1})

# Profitability flag
df['is_profit'] = df['PnL'] > 0

# ---------------------------
# Analysis 1: PnL vs Sentiment
# ---------------------------
pnl_by_sentiment = df.groupby('classification')['PnL'].mean()
print("Average PnL by Sentiment:\n", pnl_by_sentiment)

# ---------------------------
# Analysis 2: Win Rate
# ---------------------------
win_rate = df.groupby('classification')['is_profit'].mean()
print("\nWin Rate by Sentiment:\n", win_rate)

# ---------------------------
# Analysis 3: Trade Volume
# ---------------------------
trade_count = df.groupby('classification').size()
print("\nTrade Count:\n", trade_count)

# ---------------------------
# Visualization
# ---------------------------
plt.figure(figsize=(8,5))
sns.barplot(x=pnl_by_sentiment.index, y=pnl_by_sentiment.values)
plt.title("Average PnL by Market Sentiment")
plt.ylabel("Average PnL")
plt.show()

plt.figure(figsize=(8,5))
sns.barplot(x=win_rate.index, y=win_rate.values)
plt.title("Win Rate by Sentiment")
plt.ylabel("Win Rate")
plt.show()

# ---------------------------
# Advanced: Leverage Behavior
# ---------------------------
if 'leverage' in df.columns:
	leverage_analysis = df.groupby('classification')['leverage'].mean()
	print("\nAverage Leverage:\n", leverage_analysis)

	plt.figure(figsize=(8,5))
	sns.barplot(x=leverage_analysis.index, y=leverage_analysis.values)
	plt.title("Leverage Usage by Sentiment")
	plt.show()
else:
	print("\nLeverage column not found, skipping leverage analysis.")

# ---------------------------
# Save Results
# ---------------------------
df.to_csv("processed_trader_data.csv", index=False)
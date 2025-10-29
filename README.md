# Option Pricing Helper

A Python-based option trading pricing helper that calculates risk, reward, trade decay, and exit points for both buying and selling options.

## Features

- **Risk & Reward Calculations**: Calculate actual risk and reward amounts based on trade type (BUY/SELL)
- **Trade Decay**: Calculate time decay based on theta and trade duration
- **Exit Points**: Calculate take profit and stop loss levels
- **REST API**: Flask-based API server for integration with other applications
- **Batch Processing**: Calculate multiple trades simultaneously
- **Future Ready**: Structured for future option chain integration

## Calculations

### Trade Decay
```
Trade Decay = Theta / (24 * 60) * Trade Time (minutes)
```

### Exit Take Profit
- **BUY**: `Entry + Delta * Reward - Trade Decay`
- **SELL**: `Entry - Delta * Reward - Trade Decay`

### Exit Stop Loss
- **BUY**: `Entry - Delta * Risk - Trade Decay`
- **SELL**: `Entry + Delta * Risk - Trade Decay`

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Usage

Run the main calculation example:
```bash
python option_pricing_helper.py
```

Run tests:
```bash
python test_calculations.py
```

### API Server Usage

Start the Flask API server:
```bash
python api_server.py
```

The server will start on `http://localhost:5000`

#### API Endpoints

**Health Check**
```bash
GET /health
```

**Calculate Single Trade**
```bash
POST /calculate
Content-Type: application/json

{
    "delta": 0.5,
    "theta": -0.05,
    "trade_time": 30,
    "risk": 100,
    "reward": 200,
    "entry": 10.0,
    "trade_type": "buy"
}
```

**Calculate Multiple Trades**
```bash
POST /calculate-batch
Content-Type: application/json

{
    "trades": [
        {
            "delta": 0.5,
            "theta": -0.05,
            "trade_time": 30,
            "risk": 100,
            "reward": 200,
            "entry": 10.0,
            "trade_type": "buy"
        },
        {
            "delta": 0.3,
            "theta": -0.03,
            "trade_time": 45,
            "risk": 150,
            "reward": 300,
            "entry": 8.0,
            "trade_type": "sell"
        }
    ]
}
```

**Option Chain (Placeholder)**
```bash
GET /option-chain?symbol=AAPL&expiration=2024-01-19
```

### Python Library Usage

```python
from option_pricing_helper import OptionPricingHelper, OptionTradeInputs, TradeType

# Create helper instance
helper = OptionPricingHelper()

# Create trade inputs
inputs = OptionTradeInputs(
    delta=0.5,
    theta=-0.05,
    trade_time=30,  # 30 minutes
    risk=100,
    reward=200,
    entry=10.0,
    trade_type=TradeType.BUY
)

# Calculate results
results = helper.calculate_option_trade(inputs)

print(f"Trade Decay: ${results.trade_decay:.6f}")
print(f"Exit Take Profit: ${results.exit_take_profit:.4f}")
print(f"Exit Stop Loss: ${results.exit_stop_loss:.4f}")
```

## API Examples

### cURL Examples

**Single Trade Calculation:**
```bash
curl -X POST http://localhost:5000/calculate \
  -H 'Content-Type: application/json' \
  -d '{
    "delta": 0.5,
    "theta": -0.05,
    "trade_time": 30,
    "risk": 100,
    "reward": 200,
    "entry": 10.0,
    "trade_type": "buy"
  }'
```

**Health Check:**
```bash
curl http://localhost:5000/health
```

### Python Requests Examples

```python
import requests
import json

# Calculate single trade
url = "http://localhost:5000/calculate"
data = {
    "delta": 0.5,
    "theta": -0.05,
    "trade_time": 30,
    "risk": 100,
    "reward": 200,
    "entry": 10.0,
    "trade_type": "buy"
}

response = requests.post(url, json=data)
result = response.json()
print(json.dumps(result, indent=2))
```

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| delta | float | Option delta (sensitivity to underlying price) |
| theta | float | Option theta (time decay per day) |
| trade_time | float | Time in minutes for the trade |
| risk | float | Risk amount |
| reward | float | Reward amount |
| entry | float | Entry price of the option |
| trade_type | string | "buy" or "sell" |

## Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| trade_decay | float | Calculated time decay for the trade |
| exit_take_profit | float | Price level for taking profit |
| exit_stop_loss | float | Price level for stopping loss |
| risk_amount | float | Actual risk amount |
| reward_amount | float | Actual reward amount |

## Future Enhancements

- Real-time option chain integration
- Historical data analysis
- Risk management tools
- Portfolio optimization
- Advanced Greeks calculations
- Market data feeds integration

## Files Structure

```
op_helper/
├── option_pricing_helper.py  # Main calculation logic
├── api_server.py             # Flask REST API server
├── test_calculations.py      # Test suite
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Testing

The project includes comprehensive tests in `test_calculations.py`. Run tests to verify calculations:

```bash
python test_calculations.py
```

Tests cover:
- BUY option calculations
- SELL option calculations
- Edge cases (zero theta, different time periods, high delta)
- Manual verification of formulas

## License

This project is provided as-is for educational and development purposes.
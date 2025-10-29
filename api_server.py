"""
API Server for Option Pricing Helper
====================================

Flask-based REST API server for option pricing calculations.
Provides endpoints for trade calculations and future option chain integration.
"""

from flask import Flask, request, jsonify
from option_pricing_helper import OptionPricingHelper, OptionTradeInputs, TradeType
from config_manager import ConfigManager
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
config_manager = ConfigManager()
helper = OptionPricingHelper(config_manager)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Option Pricing Helper API"})


@app.route('/calculate', methods=['POST'])
def calculate_option_trade():
    """
    Calculate option trade metrics
    
    Expected JSON payload:
    {
        "delta": 0.5,
        "theta": -0.05,
        "trade_time": 30,
        "risk": 100,
        "reward": 200,
        "entry": 10.0,
        "trade_type": "buy"  // or "sell"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['delta', 'theta', 'trade_time', 'risk', 'reward', 'entry', 'trade_type']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }), 400
        
        # Validate trade_type
        trade_type_str = data['trade_type'].lower()
        if trade_type_str not in ['buy', 'sell']:
            return jsonify({
                "error": "Invalid trade_type. Must be 'buy' or 'sell'"
            }), 400
        
        # Create trade inputs
        trade_type = TradeType.BUY if trade_type_str == 'buy' else TradeType.SELL
        
        inputs = OptionTradeInputs(
            delta=float(data['delta']),
            theta=float(data['theta']),
            trade_time=float(data['trade_time']),
            risk=float(data['risk']),
            reward=float(data['reward']),
            entry=float(data['entry']),
            trade_type=trade_type
        )
        
        # Calculate results
        results = helper.calculate_option_trade(inputs)
        
        # Return results
        response_data = {
            "success": True,
            "inputs": {
                "delta": inputs.delta,
                "theta": inputs.theta,
                "trade_time": inputs.trade_time,
                "risk": inputs.risk,
                "reward": inputs.reward,
                "entry": inputs.entry,
                "trade_type": inputs.trade_type.value
            },
            "results": {
                "trade_decay": round(results.trade_decay, 6),
                "exit_take_profit": round(results.exit_take_profit, 4),
                "exit_stop_loss": round(results.exit_stop_loss, 4),
                "risk_amount": results.risk_amount,
                "reward_amount": results.reward_amount
            }
        }
        
        # Add risk validation if available
        if results.risk_validation:
            response_data["risk_validation"] = results.risk_validation
        
        return jsonify(response_data)
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid input values",
            "message": str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Calculation error: {str(e)}")
        return jsonify({
            "error": "Internal calculation error",
            "message": str(e)
        }), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        config = config_manager.get_config()
        if config:
            return jsonify({
                "success": True,
                "config": {
                    "total_capital": config.total_capital,
                    "risk_per_trade_percentage": config.risk_per_trade_percentage,
                    "max_risk_per_trade": config.max_risk_per_trade,
                    "created_at": config.created_at,
                    "updated_at": config.updated_at
                }
            })
        else:
            return jsonify({
                "error": "Configuration not found"
            }), 404
    except Exception as e:
        logger.error(f"Config retrieval error: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve configuration",
            "message": str(e)
        }), 500


@app.route('/config', methods=['POST'])
def update_config():
    """
    Update configuration
    
    Expected JSON payload:
    {
        "total_capital": 10000,
        "risk_per_trade_percentage": 2.0
    }
    """
    try:
        data = request.get_json()
        
        total_capital = data.get('total_capital')
        risk_percentage = data.get('risk_per_trade_percentage')
        
        if total_capital is not None and total_capital <= 0:
            return jsonify({
                "error": "Total capital must be positive"
            }), 400
        
        if risk_percentage is not None and (risk_percentage <= 0 or risk_percentage > 100):
            return jsonify({
                "error": "Risk percentage must be between 0 and 100"
            }), 400
        
        success = config_manager.update_config(
            total_capital=total_capital,
            risk_per_trade_percentage=risk_percentage
        )
        
        if success:
            config = config_manager.get_config()
            return jsonify({
                "success": True,
                "message": "Configuration updated successfully",
                "config": {
                    "total_capital": config.total_capital,
                    "risk_per_trade_percentage": config.risk_per_trade_percentage,
                    "max_risk_per_trade": config.max_risk_per_trade,
                    "updated_at": config.updated_at
                }
            })
        else:
            return jsonify({
                "error": "Failed to update configuration"
            }), 500
            
    except Exception as e:
        logger.error(f"Config update error: {str(e)}")
        return jsonify({
            "error": "Failed to update configuration",
            "message": str(e)
        }), 500


@app.route('/validate-risk', methods=['POST'])
def validate_risk():
    """
    Validate risk amount against configuration
    
    Expected JSON payload:
    {
        "risk_amount": 250
    }
    """
    try:
        data = request.get_json()
        
        if 'risk_amount' not in data:
            return jsonify({
                "error": "Missing required field: risk_amount"
            }), 400
        
        risk_amount = float(data['risk_amount'])
        validation_result = config_manager.validate_risk(risk_amount)
        
        return jsonify({
            "success": True,
            "validation": {
                "is_valid": validation_result.is_valid,
                "risk_amount": validation_result.risk_amount,
                "max_allowed_risk": validation_result.max_allowed_risk,
                "risk_percentage_of_capital": validation_result.risk_percentage_of_capital,
                "configured_max_percentage": validation_result.configured_max_percentage,
                "is_over_limit": validation_result.is_over_limit,
                "warning_message": validation_result.warning_message,
                "severity": validation_result.severity
            }
        })
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid risk amount",
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Risk validation error: {str(e)}")
        return jsonify({
            "error": "Risk validation failed",
            "message": str(e)
        }), 500


@app.route('/position-size', methods=['POST'])
def suggest_position_size():
    """
    Suggest position size based on risk parameters
    
    Expected JSON payload:
    {
        "risk_amount": 200,
        "entry_price": 10.0,
        "stop_loss_price": 8.0
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['risk_amount', 'entry_price', 'stop_loss_price']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }), 400
        
        suggestion = config_manager.get_position_size_suggestion(
            risk_amount=float(data['risk_amount']),
            entry_price=float(data['entry_price']),
            stop_loss_price=float(data['stop_loss_price'])
        )
        
        return jsonify({
            "success": True,
            "suggestion": suggestion
        })
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid input values",
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Position sizing error: {str(e)}")
        return jsonify({
            "error": "Position sizing failed",
            "message": str(e)
        }), 500


@app.route('/option-chain', methods=['GET'])
def get_option_chain():
    """
    Placeholder endpoint for future option chain integration
    
    Query parameters:
    - symbol: Stock symbol (e.g., AAPL)
    - expiration: Expiration date (YYYY-MM-DD)
    """
    symbol = request.args.get('symbol')
    expiration = request.args.get('expiration')
    
    if not symbol:
        return jsonify({
            "error": "Missing required parameter: symbol"
        }), 400
    
    # Placeholder response - to be implemented with actual option chain API
    return jsonify({
        "message": "Option chain endpoint not yet implemented",
        "symbol": symbol,
        "expiration": expiration,
        "note": "This endpoint will be implemented to fetch real option chain data"
    }), 501


@app.route('/calculate-batch', methods=['POST'])
def calculate_batch():
    """
    Calculate multiple option trades in batch
    
    Expected JSON payload:
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
            // ... more trades
        ]
    }
    """
    try:
        data = request.get_json()
        
        if 'trades' not in data or not isinstance(data['trades'], list):
            return jsonify({
                "error": "Expected 'trades' array in request body"
            }), 400
        
        results = []
        errors = []
        
        for i, trade_data in enumerate(data['trades']):
            try:
                # Validate required fields for this trade
                required_fields = ['delta', 'theta', 'trade_time', 'risk', 'reward', 'entry', 'trade_type']
                missing_fields = [field for field in required_fields if field not in trade_data]
                
                if missing_fields:
                    errors.append({
                        "trade_index": i,
                        "error": "Missing required fields",
                        "missing_fields": missing_fields
                    })
                    continue
                
                # Validate trade_type
                trade_type_str = trade_data['trade_type'].lower()
                if trade_type_str not in ['buy', 'sell']:
                    errors.append({
                        "trade_index": i,
                        "error": "Invalid trade_type. Must be 'buy' or 'sell'"
                    })
                    continue
                
                # Create trade inputs
                trade_type = TradeType.BUY if trade_type_str == 'buy' else TradeType.SELL
                
                inputs = OptionTradeInputs(
                    delta=float(trade_data['delta']),
                    theta=float(trade_data['theta']),
                    trade_time=float(trade_data['trade_time']),
                    risk=float(trade_data['risk']),
                    reward=float(trade_data['reward']),
                    entry=float(trade_data['entry']),
                    trade_type=trade_type
                )
                
                # Calculate results
                trade_results = helper.calculate_option_trade(inputs)
                
                results.append({
                    "trade_index": i,
                    "inputs": {
                        "delta": inputs.delta,
                        "theta": inputs.theta,
                        "trade_time": inputs.trade_time,
                        "risk": inputs.risk,
                        "reward": inputs.reward,
                        "entry": inputs.entry,
                        "trade_type": inputs.trade_type.value
                    },
                    "results": {
                        "trade_decay": round(trade_results.trade_decay, 6),
                        "exit_take_profit": round(trade_results.exit_take_profit, 4),
                        "exit_stop_loss": round(trade_results.exit_stop_loss, 4),
                        "risk_amount": trade_results.risk_amount,
                        "reward_amount": trade_results.reward_amount
                    }
                })
                
            except Exception as e:
                errors.append({
                    "trade_index": i,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "processed_trades": len(results),
            "errors": len(errors),
            "results": results,
            "errors_detail": errors if errors else None
        })
        
    except Exception as e:
        logger.error(f"Batch calculation error: {str(e)}")
        return jsonify({
            "error": "Internal batch calculation error",
            "message": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /health - Health check",
            "POST /calculate - Calculate single option trade",
            "POST /calculate-batch - Calculate multiple option trades",
            "GET /option-chain - Get option chain (placeholder)"
        ]
    }), 404


if __name__ == '__main__':
    print("Starting Option Pricing Helper API Server...")
    print("Available endpoints:")
    print("  GET  /health - Health check")
    print("  POST /calculate - Calculate option trade")
    print("  POST /calculate-batch - Calculate multiple trades")
    print("  GET  /option-chain - Option chain (placeholder)")
    print("\nExample usage:")
    print("curl -X POST http://localhost:5000/calculate \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"delta\":0.5,\"theta\":-0.05,\"trade_time\":30,\"risk\":100,\"reward\":200,\"entry\":10.0,\"trade_type\":\"buy\"}'")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
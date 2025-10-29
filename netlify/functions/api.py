"""
Netlify Function for Option Pricing Helper API
==============================================

This function serves as the main API endpoint for Netlify deployment.
It handles all API routes through a single serverless function.
"""

import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from option_pricing_helper import OptionPricingHelper, OptionTradeInputs, TradeType
from config_manager import ConfigManager
from dataclasses import asdict


def handler(event, context):
    """Main handler for Netlify function"""
    
    # Initialize components
    config_manager = ConfigManager()
    helper = OptionPricingHelper(config_manager)
    
    # Get HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '').replace('/.netlify/functions/api', '')
    
    # Parse request body for POST requests
    body = {}
    if http_method in ['POST', 'PUT'] and event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Invalid JSON in request body'
                })
            }
    
    # Handle CORS preflight requests
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            }
        }
    
    try:
        # Route handling
        if path == '/health' and http_method == 'GET':
            return handle_health()
        elif path == '/calculate' and http_method == 'POST':
            return handle_calculate(body, helper)
        elif path == '/config' and http_method == 'GET':
            return handle_get_config(config_manager)
        elif path == '/config' and http_method == 'POST':
            return handle_update_config(body, config_manager)
        elif path == '/validate-risk' and http_method == 'POST':
            return handle_validate_risk(body, config_manager)
        elif path == '/position-size' and http_method == 'POST':
            return handle_position_size(body, config_manager)
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Endpoint not found',
                    'available_endpoints': [
                        'GET /health',
                        'POST /calculate',
                        'GET /config',
                        'POST /config',
                        'POST /validate-risk',
                        'POST /position-size'
                    ]
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def get_cors_headers():
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    }


def handle_health():
    """Handle health check"""
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'status': 'healthy',
            'service': 'Option Pricing Helper API (Netlify)'
        })
    }


def handle_calculate(body, helper):
    """Handle option calculation"""
    try:
        # Validate required fields
        required_fields = ['delta', 'theta', 'trade_time', 'risk', 'reward', 'entry', 'trade_type']
        missing_fields = [field for field in required_fields if field not in body]
        
        if missing_fields:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                })
            }
        
        # Validate trade_type
        trade_type_str = body['trade_type'].lower()
        if trade_type_str not in ['buy', 'sell']:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Invalid trade_type. Must be "buy" or "sell"'
                })
            }
        
        # Create trade inputs
        trade_type = TradeType.BUY if trade_type_str == 'buy' else TradeType.SELL
        
        inputs = OptionTradeInputs(
            delta=float(body['delta']),
            theta=float(body['theta']),
            trade_time=float(body['trade_time']),
            risk=float(body['risk']),
            reward=float(body['reward']),
            entry=float(body['entry']),
            trade_type=trade_type
        )
        
        # Calculate results
        results = helper.calculate_option_trade(inputs)
        
        # Prepare response
        response_data = {
            'success': True,
            'inputs': {
                'delta': inputs.delta,
                'theta': inputs.theta,
                'trade_time': inputs.trade_time,
                'risk': inputs.risk,
                'reward': inputs.reward,
                'entry': inputs.entry,
                'trade_type': inputs.trade_type.value
            },
            'results': {
                'trade_decay': round(results.trade_decay, 6),
                'exit_take_profit': round(results.exit_take_profit, 4),
                'exit_stop_loss': round(results.exit_stop_loss, 4),
                'risk_amount': results.risk_amount,
                'reward_amount': results.reward_amount
            }
        }
        
        # Add risk validation if available
        if results.risk_validation:
            response_data['risk_validation'] = results.risk_validation
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response_data)
        }
        
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Invalid input values',
                'message': str(e)
            })
        }


def handle_get_config(config_manager):
    """Handle get configuration"""
    try:
        config = config_manager.get_config()
        if config:
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': True,
                    'config': {
                        'total_capital': config.total_capital,
                        'risk_per_trade_percentage': config.risk_per_trade_percentage,
                        'max_risk_per_trade': config.max_risk_per_trade,
                        'created_at': config.created_at,
                        'updated_at': config.updated_at
                    }
                })
            }
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Configuration not found'
                })
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Failed to retrieve configuration',
                'message': str(e)
            })
        }


def handle_update_config(body, config_manager):
    """Handle update configuration"""
    try:
        total_capital = body.get('total_capital')
        risk_percentage = body.get('risk_per_trade_percentage')
        
        if total_capital is not None and total_capital <= 0:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Total capital must be positive'
                })
            }
        
        if risk_percentage is not None and (risk_percentage <= 0 or risk_percentage > 100):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Risk percentage must be between 0 and 100'
                })
            }
        
        success = config_manager.update_config(
            total_capital=total_capital,
            risk_per_trade_percentage=risk_percentage
        )
        
        if success:
            config = config_manager.get_config()
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': True,
                    'message': 'Configuration updated successfully',
                    'config': {
                        'total_capital': config.total_capital,
                        'risk_per_trade_percentage': config.risk_per_trade_percentage,
                        'max_risk_per_trade': config.max_risk_per_trade,
                        'updated_at': config.updated_at
                    }
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Failed to update configuration'
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Failed to update configuration',
                'message': str(e)
            })
        }


def handle_validate_risk(body, config_manager):
    """Handle risk validation"""
    try:
        if 'risk_amount' not in body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Missing required field: risk_amount'
                })
            }
        
        risk_amount = float(body['risk_amount'])
        validation_result = config_manager.validate_risk(risk_amount)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'validation': asdict(validation_result)
            })
        }
        
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Invalid risk amount',
                'message': str(e)
            })
        }


def handle_position_size(body, config_manager):
    """Handle position size suggestion"""
    try:
        required_fields = ['risk_amount', 'entry_price', 'stop_loss_price']
        missing_fields = [field for field in required_fields if field not in body]
        
        if missing_fields:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                })
            }
        
        suggestion = config_manager.get_position_size_suggestion(
            risk_amount=float(body['risk_amount']),
            entry_price=float(body['entry_price']),
            stop_loss_price=float(body['stop_loss_price'])
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'suggestion': suggestion
            })
        }
        
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Invalid input values',
                'message': str(e)
            })
        }
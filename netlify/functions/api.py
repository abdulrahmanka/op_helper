"""
Netlify Function for Option Pricing Helper API
==============================================

This function serves as the main API endpoint for Netlify deployment.
It handles all API routes through a single serverless function.
"""

import json
import sys
import os
from dataclasses import dataclass, asdict
from typing import Optional
from enum import Enum
from datetime import datetime

# Inline all required classes and functions
class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class OptionTradeInputs:
    """Input parameters for option trade calculations"""
    delta: float
    theta: float
    trade_time: float
    risk: float
    reward: float
    entry: float
    trade_type: TradeType

@dataclass
class OptionTradeResults:
    """Results of option trade calculations"""
    trade_decay: float
    exit_take_profit: float
    exit_stop_loss: float
    risk_amount: float
    reward_amount: float
    risk_validation: dict = None

@dataclass
class PositionSizingConfig:
    """Configuration for position sizing and risk management"""
    total_capital: float
    risk_per_trade_percentage: float
    max_risk_per_trade: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.max_risk_per_trade is None:
            self.max_risk_per_trade = self.total_capital * (self.risk_per_trade_percentage / 100.0)
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

@dataclass
class RiskValidationResult:
    """Result of risk validation"""
    is_valid: bool
    risk_amount: float
    max_allowed_risk: float
    risk_percentage_of_capital: float
    configured_max_percentage: float
    is_over_limit: bool
    warning_message: Optional[str] = None
    severity: str = "info"

class OptionPricingHelper:
    """Main class for option pricing calculations"""
    
    def __init__(self, config_manager=None):
        self.name = "Option Pricing Helper"
        self.config_manager = config_manager
    
    def calculate_trade_decay(self, theta: float, trade_time: float) -> float:
        decay_per_minute = theta / (24 * 60)
        return decay_per_minute * trade_time
    
    def calculate_risk_reward(self, trade_type: TradeType, risk: float, reward: float) -> tuple:
        return risk, reward
    
    def calculate_exit_take_profit(self, entry: float, delta: float, reward: float, 
                                 trade_decay: float, trade_type: TradeType) -> float:
        if trade_type == TradeType.BUY:
            return entry + (delta * reward) - trade_decay
        else:
            return entry - (delta * reward) - trade_decay
    
    def calculate_exit_stop_loss(self, entry: float, delta: float, risk: float,
                               trade_decay: float, trade_type: TradeType) -> float:
        if trade_type == TradeType.BUY:
            return entry - (delta * risk) - trade_decay
        else:
            return entry + (delta * risk) - trade_decay
    
    def calculate_option_trade(self, inputs: OptionTradeInputs) -> OptionTradeResults:
        trade_decay = self.calculate_trade_decay(inputs.theta, inputs.trade_time)
        risk_amount, reward_amount = self.calculate_risk_reward(
            inputs.trade_type, inputs.risk, inputs.reward
        )
        exit_take_profit = self.calculate_exit_take_profit(
            inputs.entry, inputs.delta, inputs.reward, trade_decay, inputs.trade_type
        )
        exit_stop_loss = self.calculate_exit_stop_loss(
            inputs.entry, inputs.delta, inputs.risk, trade_decay, inputs.trade_type
        )
        
        risk_validation = None
        if self.config_manager:
            validation_result = self.config_manager.validate_risk(risk_amount)
            risk_validation = asdict(validation_result)
        
        return OptionTradeResults(
            trade_decay=trade_decay,
            exit_take_profit=exit_take_profit,
            exit_stop_loss=exit_stop_loss,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_validation=risk_validation
        )

class ConfigManager:
    """Manages configuration for the option pricing helper"""
    
    def __init__(self):
        self.config = PositionSizingConfig(
            total_capital=10000.0,
            risk_per_trade_percentage=2.0
        )
    
    def get_config(self) -> PositionSizingConfig:
        return self.config
    
    def update_config(self, total_capital: Optional[float] = None, 
                     risk_per_trade_percentage: Optional[float] = None) -> bool:
        if total_capital is not None:
            self.config.total_capital = total_capital
        if risk_per_trade_percentage is not None:
            self.config.risk_per_trade_percentage = risk_per_trade_percentage
        self.config.max_risk_per_trade = self.config.total_capital * (self.config.risk_per_trade_percentage / 100.0)
        self.config.updated_at = datetime.now().isoformat()
        return True
    
    def validate_risk(self, risk_amount: float) -> RiskValidationResult:
        max_allowed_risk = self.config.max_risk_per_trade
        risk_percentage_of_capital = (risk_amount / self.config.total_capital) * 100.0
        configured_max_percentage = self.config.risk_per_trade_percentage
        is_over_limit = risk_amount > max_allowed_risk
        
        severity = "info"
        warning_message = None
        is_valid = True
        
        if is_over_limit:
            severity = "error"
            is_valid = False
            warning_message = (
                f"⚠️ RISK LIMIT EXCEEDED! Risk amount ${risk_amount:.2f} exceeds "
                f"maximum allowed ${max_allowed_risk:.2f} "
                f"({risk_percentage_of_capital:.2f}% > {configured_max_percentage}% of capital)"
            )
        elif risk_percentage_of_capital > (configured_max_percentage * 0.8):
            severity = "warning"
            warning_message = (
                f"⚠️ High Risk Warning: Risk amount ${risk_amount:.2f} is approaching "
                f"the limit of ${max_allowed_risk:.2f} "
                f"({risk_percentage_of_capital:.2f}% of {configured_max_percentage}% max)"
            )
        else:
            warning_message = (
                f"✅ Risk within limits: ${risk_amount:.2f} "
                f"({risk_percentage_of_capital:.2f}% of capital)"
            )
        
        return RiskValidationResult(
            is_valid=is_valid,
            risk_amount=risk_amount,
            max_allowed_risk=max_allowed_risk,
            risk_percentage_of_capital=risk_percentage_of_capital,
            configured_max_percentage=configured_max_percentage,
            is_over_limit=is_over_limit,
            warning_message=warning_message,
            severity=severity
        )
    
    def get_position_size_suggestion(self, risk_amount: float, entry_price: float, 
                                   stop_loss_price: float) -> dict:
        risk_per_option = abs(entry_price - stop_loss_price)
        
        if risk_per_option <= 0:
            return {
                "error": "Invalid price levels - entry and stop loss must be different",
                "suggested_contracts": 0
            }
        
        max_contracts = int(risk_amount / risk_per_option)
        actual_risk = max_contracts * risk_per_option
        risk_validation = self.validate_risk(actual_risk)
        
        return {
            "suggested_contracts": max_contracts,
            "risk_per_option": risk_per_option,
            "actual_risk": actual_risk,
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "total_capital": self.config.total_capital,
            "max_allowed_risk": self.config.max_risk_per_trade,
            "risk_validation": asdict(risk_validation)
        }


def handler(event, context):
    """Main handler for Netlify function"""
    
    # Initialize components
    config_manager = ConfigManager()
    helper = OptionPricingHelper(config_manager)
    
    # Get HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    
    # Extract path from different possible locations
    path = event.get('path', '')
    if path.startswith('/.netlify/functions/api'):
        path = path.replace('/.netlify/functions/api', '')
    
    # Handle query parameters for different endpoint detection
    query_params = event.get('queryStringParameters') or {}
    
    # If path is still empty, try to determine from rawUrl or just default to health
    if not path or path == '/':
        path = '/health'
        
    # Log for debugging (will appear in Netlify function logs)
    print(f"Request: {http_method} {path}")
    
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
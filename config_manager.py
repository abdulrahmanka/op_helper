"""
Configuration Manager for Option Pricing Helper
===============================================

Manages global configuration including total capital, risk per trade percentage,
and position sizing settings. Provides risk validation and alerts.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class PositionSizingConfig:
    """Configuration for position sizing and risk management"""
    total_capital: float
    risk_per_trade_percentage: float  # As percentage (e.g., 2.0 for 2%)
    max_risk_per_trade: Optional[float] = None  # Auto-calculated from percentage
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Calculate max risk per trade and set timestamps"""
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
    severity: str = "info"  # "info", "warning", "error"


class ConfigManager:
    """Manages configuration for the option pricing helper"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Optional[PositionSizingConfig] = None
        self.load_config()
    
    def load_config(self) -> Optional[PositionSizingConfig]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.config = PositionSizingConfig(**data)
                    return self.config
            else:
                # Create default config if file doesn't exist
                self.config = self.create_default_config()
                self.save_config()
                return self.config
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.create_default_config()
            return self.config
    
    def create_default_config(self) -> PositionSizingConfig:
        """Create default configuration"""
        return PositionSizingConfig(
            total_capital=10000.0,  # Default $10,000
            risk_per_trade_percentage=2.0  # Default 2%
        )
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            if self.config:
                # Update the timestamp
                self.config.updated_at = datetime.now().isoformat()
                # Recalculate max risk
                self.config.max_risk_per_trade = self.config.total_capital * (self.config.risk_per_trade_percentage / 100.0)
                
                with open(self.config_file, 'w') as f:
                    json.dump(asdict(self.config), f, indent=2)
                return True
        except Exception as e:
            print(f"Error saving config: {e}")
        return False
    
    def update_config(self, total_capital: Optional[float] = None, 
                     risk_per_trade_percentage: Optional[float] = None) -> bool:
        """Update configuration values"""
        try:
            if self.config is None:
                self.config = self.create_default_config()
            
            if total_capital is not None:
                self.config.total_capital = total_capital
            
            if risk_per_trade_percentage is not None:
                self.config.risk_per_trade_percentage = risk_per_trade_percentage
            
            # Recalculate max risk per trade
            self.config.max_risk_per_trade = self.config.total_capital * (self.config.risk_per_trade_percentage / 100.0)
            
            return self.save_config()
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def get_config(self) -> Optional[PositionSizingConfig]:
        """Get current configuration"""
        return self.config
    
    def validate_risk(self, risk_amount: float) -> RiskValidationResult:
        """
        Validate if the risk amount is within acceptable limits
        
        Args:
            risk_amount: The risk amount to validate
            
        Returns:
            RiskValidationResult with validation details
        """
        if self.config is None:
            self.config = self.create_default_config()
        
        max_allowed_risk = self.config.max_risk_per_trade
        risk_percentage_of_capital = (risk_amount / self.config.total_capital) * 100.0
        configured_max_percentage = self.config.risk_per_trade_percentage
        is_over_limit = risk_amount > max_allowed_risk
        
        # Determine severity and message
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
        elif risk_percentage_of_capital > (configured_max_percentage * 0.8):  # 80% of max
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
                                   stop_loss_price: float) -> Dict[str, Any]:
        """
        Suggest position size based on risk amount and price levels
        
        Args:
            risk_amount: Amount willing to risk
            entry_price: Entry price per option
            stop_loss_price: Stop loss price per option
            
        Returns:
            Dictionary with position sizing suggestions
        """
        if self.config is None:
            self.config = self.create_default_config()
        
        # Calculate risk per option contract
        risk_per_option = abs(entry_price - stop_loss_price)
        
        if risk_per_option <= 0:
            return {
                "error": "Invalid price levels - entry and stop loss must be different",
                "suggested_contracts": 0
            }
        
        # Calculate maximum number of contracts based on risk
        max_contracts = int(risk_amount / risk_per_option)
        
        # Calculate actual risk with suggested contracts
        actual_risk = max_contracts * risk_per_option
        
        # Get risk validation
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
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        try:
            self.config = self.create_default_config()
            return self.save_config()
        except Exception as e:
            print(f"Error resetting config: {e}")
            return False


def main():
    """Example usage of the ConfigManager"""
    print("=== Configuration Manager Example ===")
    
    # Create config manager
    config_manager = ConfigManager("example_config.json")
    
    # Display current config
    config = config_manager.get_config()
    print(f"\nCurrent Configuration:")
    print(f"  Total Capital: ${config.total_capital:,.2f}")
    print(f"  Risk Per Trade: {config.risk_per_trade_percentage}%")
    print(f"  Max Risk Per Trade: ${config.max_risk_per_trade:,.2f}")
    
    # Test risk validation
    print(f"\n=== Risk Validation Tests ===")
    
    test_risks = [100, 200, 250, 300]
    for risk in test_risks:
        validation = config_manager.validate_risk(risk)
        print(f"\nRisk ${risk}:")
        print(f"  {validation.warning_message}")
        print(f"  Severity: {validation.severity}")
        print(f"  Valid: {validation.is_valid}")
    
    # Test position sizing
    print(f"\n=== Position Sizing Example ===")
    suggestion = config_manager.get_position_size_suggestion(
        risk_amount=200,
        entry_price=10.0,
        stop_loss_price=8.0
    )
    
    print(f"Position Size Suggestion:")
    print(f"  Suggested Contracts: {suggestion['suggested_contracts']}")
    print(f"  Risk Per Option: ${suggestion['risk_per_option']:.2f}")
    print(f"  Actual Risk: ${suggestion['actual_risk']:.2f}")
    
    # Update configuration
    print(f"\n=== Updating Configuration ===")
    config_manager.update_config(total_capital=15000, risk_per_trade_percentage=1.5)
    updated_config = config_manager.get_config()
    print(f"Updated Configuration:")
    print(f"  Total Capital: ${updated_config.total_capital:,.2f}")
    print(f"  Risk Per Trade: {updated_config.risk_per_trade_percentage}%")
    print(f"  Max Risk Per Trade: ${updated_config.max_risk_per_trade:,.2f}")


if __name__ == "__main__":
    main()
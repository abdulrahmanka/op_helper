"""
Option Pricing Helper for Trade Risk/Reward Calculations
========================================================

This module provides calculations for option trading including:
- Risk and reward calculations for buy/sell positions
- Trade decay based on theta and time
- Exit points for take profit and stop loss
"""

from dataclasses import dataclass, asdict
from typing import Literal, Optional
from enum import Enum


class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class OptionTradeInputs:
    """Input parameters for option trade calculations"""
    delta: float  # Option delta
    theta: float  # Option theta (daily decay)
    trade_time: float  # Time in minutes
    risk: float  # Risk amount
    reward: float  # Reward amount
    entry: float  # Entry price
    trade_type: TradeType  # BUY or SELL


@dataclass
class OptionTradeResults:
    """Results of option trade calculations"""
    trade_decay: float
    exit_take_profit: float
    exit_stop_loss: float
    risk_amount: float
    reward_amount: float
    risk_validation: dict = None  # Risk validation results


class OptionPricingHelper:
    """Main class for option pricing calculations"""
    
    def __init__(self, config_manager=None):
        self.name = "Option Pricing Helper"
        self.config_manager = config_manager
    
    def calculate_trade_decay(self, theta: float, trade_time: float) -> float:
        """
        Calculate trade decay based on theta and time
        
        Args:
            theta: Option theta (daily decay)
            trade_time: Time in minutes
            
        Returns:
            Trade decay amount
        """
        # Convert theta from daily to per-minute and multiply by trade time
        decay_per_minute = theta / (24 * 60)
        return decay_per_minute * trade_time
    
    def calculate_risk_reward(self, trade_type: TradeType, risk: float, reward: float) -> tuple[float, float]:
        """
        Calculate actual risk and reward amounts based on trade type
        
        Args:
            trade_type: BUY or SELL
            risk: Risk input
            reward: Reward input
            
        Returns:
            Tuple of (risk_amount, reward_amount)
        """
        if trade_type == TradeType.BUY:
            # For buying options, risk and reward are as provided
            return risk, reward
        else:  # SELL
            # For selling options, risk and reward calculations may differ
            # Using the same values for now, but this can be customized
            return risk, reward
    
    def calculate_exit_take_profit(self, entry: float, delta: float, reward: float, 
                                 trade_decay: float, trade_type: TradeType) -> float:
        """
        Calculate exit take profit price
        
        Args:
            entry: Entry price
            delta: Option delta
            reward: Reward amount
            trade_decay: Trade decay amount
            trade_type: BUY or SELL
            
        Returns:
            Exit take profit price
        """
        if trade_type == TradeType.BUY:
            # For BUY: Entry + Delta*Reward - Trade Decay
            return entry + (delta * reward) - trade_decay
        else:  # SELL
            # For SELL: Entry - Delta*Reward - Trade Decay
            return entry - (delta * reward) - trade_decay
    
    def calculate_exit_stop_loss(self, entry: float, delta: float, risk: float,
                               trade_decay: float, trade_type: TradeType) -> float:
        """
        Calculate exit stop loss price
        
        Args:
            entry: Entry price
            delta: Option delta
            risk: Risk amount
            trade_decay: Trade decay amount
            trade_type: BUY or SELL
            
        Returns:
            Exit stop loss price
        """
        if trade_type == TradeType.BUY:
            # For BUY: Entry - Delta*Risk - Trade Decay
            return entry - (delta * risk) - trade_decay
        else:  # SELL
            # For SELL: Entry + Delta*Risk - Trade Decay
            return entry + (delta * risk) - trade_decay
    
    def calculate_option_trade(self, inputs: OptionTradeInputs) -> OptionTradeResults:
        """
        Main calculation method for option trade
        
        Args:
            inputs: OptionTradeInputs object with all required parameters
            
        Returns:
            OptionTradeResults object with all calculated values
        """
        # Calculate trade decay
        trade_decay = self.calculate_trade_decay(inputs.theta, inputs.trade_time)
        
        # Calculate risk and reward amounts
        risk_amount, reward_amount = self.calculate_risk_reward(
            inputs.trade_type, inputs.risk, inputs.reward
        )
        
        # Calculate exit points
        exit_take_profit = self.calculate_exit_take_profit(
            inputs.entry, inputs.delta, inputs.reward, trade_decay, inputs.trade_type
        )
        
        exit_stop_loss = self.calculate_exit_stop_loss(
            inputs.entry, inputs.delta, inputs.risk, trade_decay, inputs.trade_type
        )
        
        # Validate risk if config manager is available
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


def main():
    """Example usage of the Option Pricing Helper"""
    helper = OptionPricingHelper()
    
    # Example for BUY option
    buy_inputs = OptionTradeInputs(
        delta=0.5,
        theta=-0.05,
        trade_time=30,  # 30 minutes
        risk=100,
        reward=200,
        entry=10.0,
        trade_type=TradeType.BUY
    )
    
    buy_results = helper.calculate_option_trade(buy_inputs)
    
    print("=== BUY Option Example ===")
    print(f"Entry Price: ${buy_inputs.entry}")
    print(f"Trade Decay: ${buy_results.trade_decay:.4f}")
    print(f"Exit Take Profit: ${buy_results.exit_take_profit:.4f}")
    print(f"Exit Stop Loss: ${buy_results.exit_stop_loss:.4f}")
    print(f"Risk Amount: ${buy_results.risk_amount}")
    print(f"Reward Amount: ${buy_results.reward_amount}")
    
    # Example for SELL option
    sell_inputs = OptionTradeInputs(
        delta=0.5,
        theta=-0.05,
        trade_time=30,  # 30 minutes
        risk=100,
        reward=200,
        entry=10.0,
        trade_type=TradeType.SELL
    )
    
    sell_results = helper.calculate_option_trade(sell_inputs)
    
    print("\n=== SELL Option Example ===")
    print(f"Entry Price: ${sell_inputs.entry}")
    print(f"Trade Decay: ${sell_results.trade_decay:.4f}")
    print(f"Exit Take Profit: ${sell_results.exit_take_profit:.4f}")
    print(f"Exit Stop Loss: ${sell_results.exit_stop_loss:.4f}")
    print(f"Risk Amount: ${sell_results.risk_amount}")
    print(f"Reward Amount: ${sell_results.reward_amount}")


if __name__ == "__main__":
    main()
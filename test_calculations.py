"""
Test script for Option Pricing Helper calculations
=================================================

This script tests the option pricing calculations with various scenarios.
"""

from option_pricing_helper import OptionPricingHelper, OptionTradeInputs, TradeType


def test_buy_option():
    """Test calculations for buying an option"""
    print("=== Testing BUY Option ===")
    
    helper = OptionPricingHelper()
    
    inputs = OptionTradeInputs(
        delta=0.5,
        theta=-0.05,
        trade_time=30,  # 30 minutes
        risk=100,
        reward=200,
        entry=10.0,
        trade_type=TradeType.BUY
    )
    
    results = helper.calculate_option_trade(inputs)
    
    print(f"Inputs:")
    print(f"  Delta: {inputs.delta}")
    print(f"  Theta: {inputs.theta}")
    print(f"  Trade Time: {inputs.trade_time} minutes")
    print(f"  Risk: ${inputs.risk}")
    print(f"  Reward: ${inputs.reward}")
    print(f"  Entry: ${inputs.entry}")
    print(f"  Trade Type: {inputs.trade_type.value}")
    
    print(f"\nResults:")
    print(f"  Trade Decay: ${results.trade_decay:.6f}")
    print(f"  Exit Take Profit: ${results.exit_take_profit:.4f}")
    print(f"  Exit Stop Loss: ${results.exit_stop_loss:.4f}")
    print(f"  Risk Amount: ${results.risk_amount}")
    print(f"  Reward Amount: ${results.reward_amount}")
    
    # Manual verification
    expected_decay = (-0.05 / (24 * 60)) * 30  # -0.001041667
    expected_take_profit = 10.0 + (0.5 * 200) - expected_decay  # 10 + 100 + 0.001041667 = 110.001041667
    expected_stop_loss = 10.0 - (0.5 * 100) - expected_decay  # 10 - 50 + 0.001041667 = -39.998958333
    
    print(f"\nManual Verification:")
    print(f"  Expected Decay: ${expected_decay:.6f}")
    print(f"  Expected Take Profit: ${expected_take_profit:.6f}")
    print(f"  Expected Stop Loss: ${expected_stop_loss:.6f}")
    
    assert abs(results.trade_decay - expected_decay) < 1e-10, "Trade decay calculation error"
    assert abs(results.exit_take_profit - expected_take_profit) < 1e-10, "Take profit calculation error"
    assert abs(results.exit_stop_loss - expected_stop_loss) < 1e-10, "Stop loss calculation error"
    
    print("✅ BUY option test passed!")


def test_sell_option():
    """Test calculations for selling an option"""
    print("\n=== Testing SELL Option ===")
    
    helper = OptionPricingHelper()
    
    inputs = OptionTradeInputs(
        delta=0.5,
        theta=-0.05,
        trade_time=30,  # 30 minutes
        risk=100,
        reward=200,
        entry=10.0,
        trade_type=TradeType.SELL
    )
    
    results = helper.calculate_option_trade(inputs)
    
    print(f"Inputs:")
    print(f"  Delta: {inputs.delta}")
    print(f"  Theta: {inputs.theta}")
    print(f"  Trade Time: {inputs.trade_time} minutes")
    print(f"  Risk: ${inputs.risk}")
    print(f"  Reward: ${inputs.reward}")
    print(f"  Entry: ${inputs.entry}")
    print(f"  Trade Type: {inputs.trade_type.value}")
    
    print(f"\nResults:")
    print(f"  Trade Decay: ${results.trade_decay:.6f}")
    print(f"  Exit Take Profit: ${results.exit_take_profit:.4f}")
    print(f"  Exit Stop Loss: ${results.exit_stop_loss:.4f}")
    print(f"  Risk Amount: ${results.risk_amount}")
    print(f"  Reward Amount: ${results.reward_amount}")
    
    # Manual verification
    expected_decay = (-0.05 / (24 * 60)) * 30  # -0.001041667
    expected_take_profit = 10.0 - (0.5 * 200) - expected_decay  # 10 - 100 + 0.001041667 = -89.998958333
    expected_stop_loss = 10.0 + (0.5 * 100) - expected_decay  # 10 + 50 + 0.001041667 = 60.001041667
    
    print(f"\nManual Verification:")
    print(f"  Expected Decay: ${expected_decay:.6f}")
    print(f"  Expected Take Profit: ${expected_take_profit:.6f}")
    print(f"  Expected Stop Loss: ${expected_stop_loss:.6f}")
    
    assert abs(results.trade_decay - expected_decay) < 1e-10, "Trade decay calculation error"
    assert abs(results.exit_take_profit - expected_take_profit) < 1e-10, "Take profit calculation error"
    assert abs(results.exit_stop_loss - expected_stop_loss) < 1e-10, "Stop loss calculation error"
    
    print("✅ SELL option test passed!")


def test_edge_cases():
    """Test edge cases and different scenarios"""
    print("\n=== Testing Edge Cases ===")
    
    helper = OptionPricingHelper()
    
    # Test with zero theta
    print("\n--- Zero Theta Test ---")
    inputs = OptionTradeInputs(
        delta=0.3,
        theta=0.0,
        trade_time=60,
        risk=50,
        reward=100,
        entry=5.0,
        trade_type=TradeType.BUY
    )
    
    results = helper.calculate_option_trade(inputs)
    print(f"Zero theta - Trade Decay: ${results.trade_decay:.6f}")
    assert results.trade_decay == 0.0, "Zero theta should result in zero decay"
    
    # Test with different time periods
    print("\n--- Different Time Periods Test ---")
    for time_minutes in [1, 15, 60, 120, 240]:
        inputs.trade_time = time_minutes
        results = helper.calculate_option_trade(inputs)
        print(f"Time: {time_minutes} min, Decay: ${results.trade_decay:.6f}")
    
    # Test with high delta
    print("\n--- High Delta Test ---")
    inputs = OptionTradeInputs(
        delta=0.9,
        theta=-0.1,
        trade_time=30,
        risk=100,
        reward=200,
        entry=15.0,
        trade_type=TradeType.BUY
    )
    
    results = helper.calculate_option_trade(inputs)
    print(f"High delta (0.9):")
    print(f"  Take Profit: ${results.exit_take_profit:.4f}")
    print(f"  Stop Loss: ${results.exit_stop_loss:.4f}")
    
    print("✅ Edge cases test passed!")


def main():
    """Run all tests"""
    print("Option Pricing Helper - Test Suite")
    print("=" * 50)
    
    try:
        test_buy_option()
        test_sell_option()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to verify discount calculation logic
"""

from decimal import Decimal

def test_discount_calculation():
    """Test the discount calculation logic"""
    
    print("🔍 TESTING DISCOUNT CALCULATION LOGIC")
    print("=" * 60)
    
    # Test case from the image
    quantity = Decimal('1.00')
    unit_price = Decimal('100000.00')
    discount_type = 'percentage'
    discount_value = Decimal('10.00')  # 10%
    
    print(f"Test Case:")
    print(f"  Quantity: {quantity}")
    print(f"  Unit Price: ₹{unit_price}")
    print(f"  Discount Type: {discount_type}")
    print(f"  Discount Value: {discount_value}%")
    print()
    
    # Calculate gross amount
    gross_amount = quantity * unit_price
    print(f"Gross Amount: {quantity} × ₹{unit_price} = ₹{gross_amount}")
    
    # Calculate discount amount
    if discount_type == 'percentage' and discount_value > 0:
        discount_amount = gross_amount * discount_value / 100
    elif discount_type == 'amount' and discount_value > 0:
        discount_amount = discount_value
    else:
        discount_amount = Decimal('0')
    
    print(f"Discount Amount: ₹{gross_amount} × {discount_value}% = ₹{discount_amount}")
    
    # Calculate final amount
    final_amount = gross_amount - discount_amount
    print(f"Final Amount: ₹{gross_amount} - ₹{discount_amount} = ₹{final_amount}")
    
    print()
    print("Expected vs Actual:")
    print(f"  Expected Discount: ₹10,000.00")
    print(f"  Actual Discount: ₹{discount_amount}")
    print(f"  Expected Final: ₹90,000.00")
    print(f"  Actual Final: ₹{final_amount}")
    
    # Check if calculations are correct
    expected_discount = Decimal('10000.00')
    expected_final = Decimal('90000.00')
    
    if discount_amount == expected_discount:
        print("✅ Discount calculation is CORRECT")
    else:
        print("❌ Discount calculation is INCORRECT")
        print(f"   Difference: ₹{discount_amount - expected_discount}")
    
    if final_amount == expected_final:
        print("✅ Final amount calculation is CORRECT")
    else:
        print("❌ Final amount calculation is INCORRECT")
        print(f"   Difference: ₹{final_amount - expected_final}")
    
    print()
    print("=" * 60)
    
    # Test with different values to see if there's a pattern
    print("🔍 TESTING WITH DIFFERENT VALUES")
    print("=" * 60)
    
    test_cases = [
        (Decimal('1'), Decimal('100'), Decimal('10'), 'percentage'),
        (Decimal('2'), Decimal('100'), Decimal('10'), 'percentage'),
        (Decimal('1'), Decimal('1000'), Decimal('10'), 'percentage'),
        (Decimal('1'), Decimal('10000'), Decimal('10'), 'percentage'),
        (Decimal('1'), Decimal('100000'), Decimal('10'), 'percentage'),
    ]
    
    for qty, price, disc_val, disc_type in test_cases:
        gross = qty * price
        if disc_type == 'percentage':
            discount = gross * disc_val / 100
        else:
            discount = disc_val
        final = gross - discount
        
        print(f"Qty: {qty}, Price: ₹{price}, Discount: {disc_val}%")
        print(f"  Gross: ₹{gross}, Discount: ₹{discount}, Final: ₹{final}")
        print()

if __name__ == "__main__":
    test_discount_calculation()

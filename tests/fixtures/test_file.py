"""
Test file for selective transformation
"""

def sum_numbers(numbers):
    """
    Sum a list of numbers.
    
    Args:
        numbers: A list of numbers to sum
        
    Returns:
        The sum of the numbers
    """
    total = 0  # Initialize total
    
    # Loop through numbers
    for num in numbers:
        total += num  # Add number to total
    
    # Print the result
    print("The sum is:", total)
    
    return total

# Test with a list of numbers
test_numbers = [1, 2, 3, 4, 5]
result = sum_numbers(test_numbers)
print("Result:", result)

# Exception handling example
try:
    invalid_numbers = [1, 2, "3"]
    sum_numbers(invalid_numbers)
except TypeError as e:
    print("Error:", e)

# Conditional example
if result > 10:
    print("Result is greater than 10")
else:
    print("Result is 10 or less")

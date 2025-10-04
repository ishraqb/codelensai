def sum_of_evens(nums):
    total = 0
    for x in nums:
        if x % 2 == 0:
            total += x
    return total

def classify(n):
    if n < 0:
        return "negative"
    elif n == 0:
        return "zero"
    else:
        return "positive"

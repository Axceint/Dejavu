def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def solve(nums):
    count = 0
    total = 0
    for v in nums:
        if is_prime(v):
            count += 1
            total += v
    return count, total


nums = list(map(int, input().split()))
c, t = solve(nums)
print(c, t)

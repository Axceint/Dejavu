def is_prime(n, i=2):
    if n < 2:
        return False
    if i * i > n:
        return True
    if n % i == 0:
        return False
    return is_prime(n, i + 1)


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

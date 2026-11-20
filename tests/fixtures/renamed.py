# Prime statistics helper
def compute_stats(values):
    """Return how many primes there are and their sum."""
    prime_count = 0
    prime_sum = 0
    for element in values:
        if check_prime(element):
            prime_count += 1
            prime_sum += element
    return prime_count, prime_sum


def check_prime(number):
    if number < 2:
        return False
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 1
    return True


data = list(map(int, input().split()))
a, b = compute_stats(data)
print(a, b)

from typing import List, Tuple


def is_prime_number(candidate: int) -> bool:
    """Determine whether the given integer is prime."""
    if candidate < 2:
        return False
    for divisor in range(2, int(candidate ** 0.5) + 1):
        if candidate % divisor == 0:
            return False
    return True


def analyze_primes(numbers: List[int]) -> Tuple[int, int]:
    """Count the primes in the list and compute their sum."""
    prime_numbers = [num for num in numbers if is_prime_number(num)]
    return len(prime_numbers), sum(prime_numbers)


def main() -> None:
    values = list(map(int, input().split()))
    prime_count, prime_total = analyze_primes(values)
    print(prime_count, prime_total)


if __name__ == "__main__":
    main()

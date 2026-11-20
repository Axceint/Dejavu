import java.util.*;
import java.util.stream.*;

public class Main {
    public static void main(String[] args) {
        Scanner s = new Scanner(System.in);
        int n = s.nextInt();
        int[] a = IntStream.range(0, n).map(k -> s.nextInt()).toArray();
        int max = Arrays.stream(a).max().orElse(0);
        BitSet composite = new BitSet(max + 1);
        for (int p = 2; (long) p * p <= max; p++)
            if (!composite.get(p))
                for (int q = p * p; q <= max; q += p) composite.set(q);
        int[] primes = Arrays.stream(a).filter(v -> v >= 2 && !composite.get(v)).toArray();
        System.out.println(primes.length + " " + Arrays.stream(primes).asLongStream().sum());
    }
}

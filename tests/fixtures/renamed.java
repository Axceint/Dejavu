import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        int size = in.nextInt();
        int primes = 0;
        long acc = 0;
        for (int j = 0; j < size; j++) {
            int val = in.nextInt();
            if (prime(val)) {
                primes++;
                acc += val;
            }
        }
        System.out.println(primes + " " + acc);
    }

    // reordered helper
    static boolean prime(int m) {
        if (m < 2) return false;
        for (int k = 2; k * k <= m; k++) {
            if (m % k == 0) return false;
        }
        return true;
    }
}

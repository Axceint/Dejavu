import java.util.Scanner;

public class Main {
    static boolean isPrime(int n) {
        if (n < 2) return false;
        for (int i = 2; i * i <= n; i++) {
            if (n % i == 0) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int count = 0;
        long total = 0;
        for (int i = 0; i < n; i++) {
            int x = sc.nextInt();
            if (isPrime(x)) {
                count++;
                total += x;
            }
        }
        System.out.println(count + " " + total);
    }
}

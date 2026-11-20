import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        String[] hw = in.readLine().trim().split(" ");
        int h = Integer.parseInt(hw[0]), w = Integer.parseInt(hw[1]);
        char[][] board = new char[h][];
        for (int i = 0; i < h; i++) board[i] = in.readLine().toCharArray();
        boolean[] vis = new boolean[h * w];
        int[] queue = new int[h * w];
        int qh = 0, qt = 0, steps = 0;
        queue[qt++] = 0;
        vis[0] = true;
        while (qh < qt) {
            int size = qt - qh;
            for (int s = 0; s < size; s++) {
                int v = queue[qh++];
                if (v == h * w - 1) {
                    System.out.println(steps);
                    return;
                }
                int x = v % w;
                int[] cand = {v - w, v + w, x > 0 ? v - 1 : -1, x + 1 < w ? v + 1 : -1};
                for (int u : cand) {
                    if (u < 0 || u >= h * w || vis[u] || board[u / w][u % w] != '.') continue;
                    vis[u] = true;
                    queue[qt++] = u;
                }
            }
            steps++;
        }
        System.out.println(-1);
    }
}

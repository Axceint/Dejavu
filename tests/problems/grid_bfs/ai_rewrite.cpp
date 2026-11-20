#include <iostream>
#include <queue>
#include <string>
#include <vector>
using namespace std;

static const int kRowDelta[4] = {1, -1, 0, 0};
static const int kColDelta[4] = {0, 0, 1, -1};

// Returns the BFS distance from the top-left to the bottom-right cell, or -1.
int shortestPath(const vector<string>& grid, int rows, int cols) {
    vector<vector<int>> distance(rows, vector<int>(cols, -1));
    queue<pair<int, int>> pending;
    distance[0][0] = 0;
    pending.push(make_pair(0, 0));
    while (!pending.empty()) {
        const int row = pending.front().first;
        const int col = pending.front().second;
        pending.pop();
        for (int dir = 0; dir < 4; ++dir) {
            const int nextRow = row + kRowDelta[dir];
            const int nextCol = col + kColDelta[dir];
            if (nextRow < 0 || nextRow >= rows || nextCol < 0 || nextCol >= cols) continue;
            if (grid[nextRow][nextCol] != '.' || distance[nextRow][nextCol] != -1) continue;
            distance[nextRow][nextCol] = distance[row][col] + 1;
            pending.push(make_pair(nextRow, nextCol));
        }
    }
    return distance[rows - 1][cols - 1];
}

int main() {
    int rows, cols;
    cin >> rows >> cols;
    vector<string> grid(rows);
    for (int i = 0; i < rows; ++i) cin >> grid[i];
    cout << shortestPath(grid, rows, cols) << '\n';
    return 0;
}

// Agota la memoria: guarda en una tabla la suma de cada tramo [i, j], O(n^2) de memoria.
// Con n = 10 000 la tabla ocupa 800 MB.
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;

    vector<vector<long long>> suma(n, vector<long long>(n));
    long long mejor = a[0];
    for (int i = 0; i < n; i++) {
        suma[i][i] = a[i];
        mejor = max(mejor, suma[i][i]);
        for (int j = i + 1; j < n; j++) {
            suma[i][j] = suma[i][j - 1] + a[j];
            mejor = max(mejor, suma[i][j]);
        }
    }
    cout << mejor << '\n';
}

// Lenta: prueba todos los tramos y suma cada uno desde cero, O(n^3).
// Es correcta, así que también sirve de fuerza bruta para `juez stress`.
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;

    long long mejor = a[0];
    for (int i = 0; i < n; i++) {
        for (int j = i; j < n; j++) {
            long long suma = 0;
            for (int k = i; k <= j; k++) suma += a[k];
            mejor = max(mejor, suma);
        }
    }
    cout << mejor << '\n';
}

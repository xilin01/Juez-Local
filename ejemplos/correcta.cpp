// Correcta: algoritmo de Kadane, O(n) en tiempo y O(1) en memoria adicional.
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;

    // actual: mejor suma de un tramo que termina en la posición i.
    long long mejor = a[0], actual = a[0];
    for (int i = 1; i < n; i++) {
        actual = max(a[i], actual + a[i]);
        mejor = max(mejor, actual);
    }
    cout << mejor << '\n';
}

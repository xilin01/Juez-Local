// Incorrecta: Kadane que arranca en 0, como si el tramo vacío fuera válido.
// Si todos los números son negativos responde 0 en lugar del mayor de ellos.
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;

    long long mejor = 0, actual = 0;
    for (int i = 0; i < n; i++) {
        actual = max(0LL, actual + a[i]);
        mejor = max(mejor, actual);
    }
    cout << mejor << '\n';
}

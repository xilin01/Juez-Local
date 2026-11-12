// Revienta: el bucle llega hasta i == n y se sale del vector.
// at() comprueba el índice y lanza std::out_of_range; nadie la captura y el programa aborta.
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;

    long long mejor = a.at(0), actual = a.at(0);
    for (int i = 1; i <= n; i++) {
        actual = max(a.at(i), actual + a.at(i));
        mejor = max(mejor, actual);
    }
    cout << mejor << '\n';
}

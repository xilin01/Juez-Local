// Programa de prueba: pide 4 GB de una sola vez.
// La reserva falla sin que el pico de memoria suba, que es el caso difícil de distinguir de un RTE.
#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<char> v(1ULL << 32, 1);
    cout << int(v[v.size() / 2]) << '\n';
}

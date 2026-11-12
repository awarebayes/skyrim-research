// Perturbed counterpart of tls_cases.cpp for the comparator's thread-local rules. It is compiled
// but never linked: each function keeps its name and instruction shape while reading another
// thread-local variable (or another member), so compared against the DLL built from
// tls_cases.cpp only the SECREL field differs and the comparison must fail on it.

extern __declspec(thread) int tls_counter;
extern __declspec(thread) int tls_guard;

struct TlsPair {
    int first;
    int second;
};
extern __declspec(thread) TlsPair tls_pair;

extern "C" __declspec(dllexport) int tls_read_counter() {
    return tls_guard;
}

extern "C" __declspec(dllexport) int tls_pair_second() {
    return tls_pair.first;
}

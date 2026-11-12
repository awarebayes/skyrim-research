// Original synthetic source for the comparator's thread-local rules (contract v2, comparator
// 0.5.0). Each exported function touches __declspec(thread) data in a different shape: a plain
// read, a read-modify-write of two variables, a member at a non-zero addend, a thread-safe
// function-local static (which reads the CRT's thread-local _Init_thread_epoch), and a catch
// funclet that reads a thread-local, so SECREL also appears outside the parent's code.
#include <stdexcept>

__declspec(thread) int tls_counter = 7;
__declspec(thread) int tls_guard;

struct TlsPair {
    int first;
    int second;
};
__declspec(thread) TlsPair tls_pair = {1, 2};

extern "C" __declspec(dllexport) __declspec(noinline) int tls_compute(int x) {
    if (x < 0) {
        throw std::runtime_error("negative");
    }
    return x * 3 + 1;
}

extern "C" __declspec(dllexport) int tls_read_counter() {
    return tls_counter;
}

extern "C" __declspec(dllexport) void tls_bump(int n) {
    tls_counter += n;
    tls_guard = 1;
}

extern "C" __declspec(dllexport) int tls_pair_second() {
    return tls_pair.second;
}

extern "C" __declspec(dllexport) int tls_static_once(int x) {
    static int value = tls_compute(x);
    return value;
}

extern "C" __declspec(dllexport) int tls_catching(int x) {
    try {
        return tls_compute(x);
    } catch (...) {
        return tls_guard;
    }
}

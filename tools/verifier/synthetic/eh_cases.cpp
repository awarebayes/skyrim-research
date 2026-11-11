// Original synthetic C++ for comparator v2 validation. It contains no game code and no
// third-party code. Each exported function makes MSVC emit one exception-handling or
// table shape the comparator must account for: unwind funclets, catch funclets with typed
// handlers, SEH scope tables, switch jump tables and chained unwind info.
// Exports keep every function alive through /OPT:REF; noinline keeps calls real, so the
// compiler cannot prove that nothing throws and drop the EH data. The functions have C++
// linkage because /EHsc assumes extern "C" functions never throw.

#include <excpt.h>

struct EhError {
    int code;
};

struct EhOtherError {
    int code;
    int extra;
};

// Non-trivial destructor: any object of this type alive across a call needs an unwind action.
struct EhGuard {
    int* slot;
    explicit EhGuard(int* s) : slot(s) { ++*slot; }
    ~EhGuard() { --*slot; }
};

static int g_eh_depth;
static int g_eh_log[16];

__declspec(dllexport) __declspec(noinline) int eh_may_throw(int value)
{
    if (value < 0) {
        throw EhError{value};
    }
    if (value > 1000) {
        throw EhOtherError{value, 7};
    }
    return value * 3;
}

// One object with a destructor alive across a throwing call: one unwind funclet, no try block.
__declspec(dllexport) int eh_guarded(int value)
{
    EhGuard guard(&g_eh_depth);
    int result = eh_may_throw(value);
    return result + g_eh_depth;
}

// Two nested objects: two unwind states, so the unwind map has a chain of actions.
__declspec(dllexport) int eh_two_guards(int value)
{
    EhGuard outer(&g_eh_depth);
    int first = eh_may_throw(value);
    EhGuard inner(&g_eh_depth);
    int second = eh_may_throw(first + 1);
    return first + second + g_eh_depth;
}

// try/catch with a typed handler, a second typed handler and catch(...): a try-block map,
// a handler array with type descriptors, catch funclets and continuation addresses.
__declspec(dllexport) int eh_catching(int value)
{
    try {
        return eh_may_throw(value) + 1;
    } catch (const EhError& error) {
        g_eh_log[0] = error.code;
        return -error.code;
    } catch (EhOtherError& other) {
        g_eh_log[1] = other.extra;
        return other.code - other.extra;
    } catch (...) {
        return -1;
    }
}

// A destructor inside a try block: unwind map and try-block map together.
__declspec(dllexport) int eh_guard_in_try(int value)
{
    int result = 0;
    try {
        EhGuard guard(&g_eh_depth);
        result = eh_may_throw(value);
    } catch (const EhError& error) {
        result = error.code * 2;
    }
    return result + g_eh_depth;
}

// Nested try blocks: a try-block map with more than one entry and nested state ranges.
__declspec(dllexport) int eh_nested(int value)
{
    int result = 0;
    try {
        try {
            result = eh_may_throw(value);
        } catch (EhOtherError& other) {
            result = eh_may_throw(other.extra - 100);
        }
    } catch (const EhError& error) {
        result = error.code + 5;
    }
    return result;
}

// Exception specification noexcept that calls a throwing function: MSVC emits EH data that
// terminates on a throw.
__declspec(dllexport) int eh_noexcept(int value) noexcept
{
    EhGuard guard(&g_eh_depth);
    return eh_may_throw(value);
}

static int eh_filter(unsigned long code)
{
    return code == 0xC0000005UL ? 1 : 0;
}

// Structured exception handling with a filter expression: __C_specific_handler with a scope
// table entry whose filter is a separate funclet.
__declspec(dllexport) int eh_seh_filter(volatile int* p)
{
    __try {
        return *p + 1;
    } __except (eh_filter(_exception_code())) {
        return -2;
    }
}

// __except(1): the scope table stores the constant instead of a filter address.
__declspec(dllexport) int eh_seh_always(volatile int* p)
{
    __try {
        return *p * 2;
    } __except (1) {
        return -3;
    }
}

// __try/__finally: a termination handler funclet and a scope entry without a jump target.
__declspec(dllexport) int eh_seh_finally(volatile int* p)
{
    int result = 0;
    __try {
        result = eh_may_throw(*p);
    } __finally {
        g_eh_log[2] = result;
    }
    return result;
}

// A dense switch: a jump table addressed relative to the image base.
__declspec(dllexport) __declspec(noinline) int eh_switch(int selector, int value)
{
    switch (selector) {
    case 0: return value + 3;
    case 1: return value * 5;
    case 2: return value - 9;
    case 3: return value ^ 0x55;
    case 4: return value << 2;
    case 5: return eh_may_throw(value);
    case 6: return value / 7;
    case 7: return value % 11;
    case 8: return -value;
    default: return 0;
    }
}

// A sparse but clustered switch: a byte index table in front of the jump table.
__declspec(dllexport) __declspec(noinline) int eh_switch_indexed(int selector)
{
    switch (selector) {
    case 10: case 12: case 19: return 1;
    case 11: case 17: return 2;
    case 13: return 3;
    case 14: case 15: case 16: return 4;
    case 18: return eh_may_throw(selector);
    case 20: return 6;
    default: return -1;
    }
}

// An early exit before any register is saved, then a long body under heavy register pressure:
// the shape for which MSVC may split the prolog and chain the later unwind info to the first.
__declspec(dllexport) __declspec(noinline) long long eh_chained(const int* data, int count, int seed)
{
    if (count <= 0 || data == nullptr) {
        return seed;
    }
    long long a = seed, b = seed * 3, c = seed ^ 5, d = seed + 7, e = 1, f = 2, g = 3, h = 4;
    for (int i = 0; i < count; ++i) {
        int v = data[i];
        a += v * b;
        b ^= a + c;
        c += eh_may_throw(v & 0xff) + d;
        d -= e * v;
        e += f ^ v;
        f += g * a;
        g ^= h + b;
        h += eh_may_throw(static_cast<int>(a & 0x3ff));
    }
    return a + b + c + d + e + f + g + h;
}

// Same idea with a cold error path that calls out with all registers live.
__declspec(dllexport) __declspec(noinline) int eh_chained_cold(int* data, int count)
{
    if (count < 4) {
        return -1;
    }
    int s0 = data[0], s1 = data[1], s2 = data[2], s3 = data[3];
    for (int i = 4; i < count; ++i) {
        int v = data[i];
        if (v == 0x7fff) {
            s0 += eh_may_throw(s1 + s2 + s3 + v);
            continue;
        }
        s0 = s0 * 31 + v;
        s1 = s1 * 17 ^ v;
        s2 += s0 - s1;
        s3 ^= s2 + v;
    }
    data[0] = s0;
    return s0 + s1 + s2 + s3;
}

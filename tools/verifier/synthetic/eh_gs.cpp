// Original synthetic C++ for comparator v2 validation, compiled with /GS so that MSVC attaches
// the security-cookie handlers. No game code and no third-party code.

#include <excpt.h>

struct GsGuard {
    int* slot;
    explicit GsGuard(int* s) : slot(s) { ++*slot; }
    ~GsGuard() { --*slot; }
};

static int g_gs_depth;

__declspec(dllexport) __declspec(noinline) int gs_fill(char* buffer, int count)
{
    for (int i = 0; i < count; ++i) {
        buffer[i] = static_cast<char>('a' + i % 26);
    }
    return count;
}

// A local array passed out: a cookie check and __GSHandlerCheck.
__declspec(dllexport) int gs_buffer(int count)
{
    char buffer[64];
    int n = gs_fill(buffer, count < 64 ? count : 64);
    return buffer[0] + buffer[n - 1];
}

// A cookie and a destructor: __GSHandlerCheck_EH, which forwards to the C++ frame handler.
__declspec(dllexport) int gs_buffer_guarded(int count)
{
    GsGuard guard(&g_gs_depth);
    char buffer[64];
    int n = gs_fill(buffer, count < 64 ? count : 64);
    return buffer[0] + n + g_gs_depth;
}

// A cookie and __try/__except: __GSHandlerCheck_SEH with a scope table.
__declspec(dllexport) int gs_buffer_seh(volatile int* p)
{
    char buffer[64];
    __try {
        int n = gs_fill(buffer, *p);
        return buffer[0] + n;
    } __except (1) {
        return -4;
    }
}

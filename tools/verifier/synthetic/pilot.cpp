// Original synthetic C++ for the compiler-worker pilot. It contains no game code and no
// third-party code. Each exported function exercises one shape the comparator must handle.
// Exports keep every function alive through /OPT:REF; noinline keeps the call shape visible.

struct PilotRecord {
    int id;
    int weight;
    int bonus;
};

static int g_pilot_total;

// Integer arithmetic only: a short leaf function with no stack frame and no calls.
extern "C" __declspec(dllexport) int pilot_mix(int a, int b)
{
    return (a * 7 + b) ^ (a >> 3);
}

// Struct field access through a pointer.
extern "C" __declspec(dllexport) int pilot_field(const PilotRecord* record)
{
    return record->weight * 3 + record->bonus;
}

// A conditional branch with two distinct results.
extern "C" __declspec(dllexport) int pilot_branch(int value)
{
    if (value < 0) {
        return -value * 2;
    }
    return value + 11;
}

// Callee for pilot_call; noinline keeps a real call instruction and a relocation.
extern "C" __declspec(dllexport) __declspec(noinline) int pilot_scale(int value, int factor)
{
    g_pilot_total += value;
    return value * factor + g_pilot_total;
}

// A call to another function, a branch around it, and work after the call so it is
// not reduced to a tail jump.
extern "C" __declspec(dllexport) int pilot_call(PilotRecord* record, int factor)
{
    if (record->id == 0) {
        return -1;
    }
    int scaled = pilot_scale(record->weight, factor);
    record->bonus = scaled;
    return scaled + record->id;
}

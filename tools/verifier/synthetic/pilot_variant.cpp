// Negative-test source: same exported name as pilot.cpp, but pilot_mix shifts by a different
// amount. A shift count is an immediate operand, so the function is expected to keep its
// length and differ only in content; comparing it against an image linked from pilot.cpp
// must fail.

extern "C" __declspec(dllexport) int pilot_mix(int a, int b)
{
    return (a * 7 + b) ^ (a >> 4);
}

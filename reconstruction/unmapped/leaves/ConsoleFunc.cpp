// Source exposure: mixed (community name; the pinned image listing).
// Code origin: original; the listing of the pinned image and the community name only
// SPDX-License-Identifier: CC0-1.0
// 0x37bff0 ConsoleFunc::FunctionToggleVolumetricLighting: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// Adapted bodies: none
#include "ConsoleFunc.h"

// g_toggleState, g_console, ConsoleMessage, the three messages and the format string: GUESS(low);
// the listing fixes only their addresses and that they are unnamed in the public map.
extern int g_toggleState;
extern void* g_console;
void ConsoleMessage(void* a_console, const char* a_format, const char* a_text);

inline int wrapState(int a_value)
{
    return a_value % 3;
}

bool ConsoleFunc::FunctionToggleVolumetricLighting()
{
    int state = wrapState(g_toggleState + 1);
    g_toggleState = state;
    const char* text = state == 1 ? "volumetric lighting on" :
                       state == 0 ? "volumetric lighting off" : "volumetric lighting toggle";
    ConsoleMessage(g_console, "Console: %s", text);
    return true;
}

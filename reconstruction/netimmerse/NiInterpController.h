// NiInterpController declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s08-niobject-niinterpcontroller
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiTimeController.h for NiTimeController.
// NiInterpController: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiInterpController::ResetTimeExtrema, NiInterpController::~NiInterpController: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include "../netimmerse/NiTimeController.h"

class NiInterpController : public NiTimeController
{
public:
    NiInterpController();
    virtual ~NiInterpController();  // compared: 0xf5fa30 (scalar deleting destructor); declared only, rule 18
};
static_assert(sizeof(NiInterpController) == 0x48, "NiInterpController size");

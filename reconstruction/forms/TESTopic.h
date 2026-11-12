// TESTopic type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESTopic.h.
// Layout beyond TESForm is not claimed. Adapted bodies: none declared.
// TESTopic, TESTopic::IsFormTypeChild: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// kInfoFormType: GUESS(low); the form type byte 0x4c the target compares against, NG's FormType::Info
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESTopic : public TESForm {
public:
    bool IsFormTypeChild(FormType a_type) override;  // 36
};

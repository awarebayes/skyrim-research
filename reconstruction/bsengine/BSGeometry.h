// BSGeometry declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bsgeometry
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiAVObject.h for NiAVObject.
// BSGeometry: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSGeometry::UpdateDownwardPass, BSGeometry::UpdateSelectedDownwardPass, BSGeometry::SetSelectiveUpdateFlags, BSGeometry::RegisterStreamables, BSGeometry::SaveBinary, BSGeometry::LoadBinary, BSGeometry::UpdateWorldBound, BSGeometry::ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiUpdateData, NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknown110: GUESS(low)
// Base-class calls and out-of-unit callees the compared code makes, declared only and bound by
// bind-hints.json: BaseUpdateDownwardPass, BaseUpdateSelectedDownwardPass,
// BaseSetSelectiveUpdateFlags, BaseRegisterStreamables, BaseSaveBinary, BaseLoadBinary,
// UpdateBoundFromFlags: GUESS(low)
// BSGeometryData110: GUESS(low); the object at +0x110, saved and loaded field by field
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiAVObject.h"

class NiUpdateData;
class NiStream;
class NiCloningProcess;

// BSGeometryData110::SaveBinaryFields, BSGeometryData110::LoadBinaryFields: GUESS(low); declared only
class BSGeometryData110
{
public:
    void SaveBinaryFields(NiStream& a_stream);
    void LoadBinaryFields(NiStream& a_stream);
    // StreamStep: GUESS(low); called three times by LoadBinary with the stream only, declared here
    static void StreamStep(NiStream& a_stream);
};

class BSGeometry : public NiAVObject
{
public:
    virtual void UpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);  // compared: 0xefc6e0
    virtual void UpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);  // compared: 0xefc720
    virtual void SetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid);  // compared: 0xefc680
    virtual bool RegisterStreamables(NiStream& a_stream);  // compared: 0xefc380
    virtual void SaveBinary(NiStream& a_stream);  // compared: 0xefc400
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xefc150
    virtual void UpdateWorldBound();  // compared: 0xefc810
    virtual void ProcessClone(NiCloningProcess& a_cloning);  // compared: 0xefc9f0

    void BaseUpdateDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
    void BaseUpdateSelectedDownwardPass(NiUpdateData& a_data, std::uint32_t a_arg2);
    void BaseSetSelectiveUpdateFlags(bool& a_selectiveUpdate, bool a_selectiveUpdateTransforms, bool& a_rigid);
    bool BaseRegisterStreamables(NiStream& a_stream);
    void BaseSaveBinary(NiStream& a_stream);
    void BaseLoadBinary(NiStream& a_stream);
    void UpdateBoundFromFlags(NiUpdateData& a_data);

    // unknown110: GUESS(low); members not recovered yet, sized so the static_assert holds
    std::uint8_t unknown110[0x48];  // 110
};
static_assert(sizeof(BSGeometry) == 0x158, "BSGeometry size");

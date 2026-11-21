// Source exposure: mixed (community names; the pinned image listing).
// SPDX-License-Identifier: CC0-1.0
// Code origin: original; the pinned image listing and the committed CrashLogger PDB names only
// Adapted bodies: none
// BSTreeNode, BSTreeNode::OnVisible: CRASHLOGGER_PDB(59818@2026.10.24)
// BSLeafAnimNode, NiCullingProcess, NodeAt180, unk000_0E0, unk0E8, unkEC, unk0F0_144, unk148, unk14C, unk150, unk151, unk152, unk153, unk154, unk158_178, unk178, unk180, unk000_120, unk120, unk121, unk000_128, unk128, unk12C: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

struct NiCullingProcess
{
    std::uint64_t unk000_120[36]; // 0x000 .. 0x11f
    std::uint8_t unk120;          // 0x120
    std::uint8_t unk121;          // 0x121
};

struct NodeAt180
{
    std::uint64_t unk000_128[37]; // 0x000 .. 0x127
    std::uint32_t unk128;         // 0x128
    std::int32_t unk12C;          // 0x12c
};

class BSLeafAnimNode
{
public:
    void OnVisible(NiCullingProcess* a_process, int a_arg);

    std::uint64_t unk000_0E0[29]; // 0x000 .. 0x0e7
    std::uint32_t unk0E8;         // 0x0e8
    float unkEC;                  // 0x0ec
    std::uint64_t unk0F0_144[11]; // 0x0f0 .. 0x147
    std::uint32_t unk148;         // 0x148
    float unk14C;                 // 0x14c
    std::uint8_t unk150;          // 0x150
    std::uint8_t unk151;          // 0x151
    std::uint8_t unk152;          // 0x152
    std::uint8_t unk153;          // 0x153
    std::uint32_t unk154;         // 0x154 .. 0x157
    std::uint64_t unk158_178[4];  // 0x158 .. 0x177
    std::uint32_t unk178;         // 0x178 .. 0x17b
};

class BSTreeNode : public BSLeafAnimNode
{
public:
    void OnVisible(NiCullingProcess* a_process, int a_arg);

    NodeAt180* unk180;            // 0x180
};

// BSShaderAccumulator functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s03-niobject-bsshaderaccumulator
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x14ecb90, 8 bytes: BSShaderAccumulator::GetCurrentAccumulator
//   RVA 0x14ecba0, 8 bytes: BSShaderAccumulator::SetCurrentAccumulator
//   RVA 0x1520d50, 21 bytes: BSShaderAccumulator::StartGroupingAlphas
//   RVA 0x151ef00, 49 bytes: BSShaderAccumulator::FinishAccumulatingPostResolveDepth
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSShaderAccumulator.h"

// ms_currentAccumulator: GUESS(low); the global slot the accessors read and write
extern BSShaderAccumulator* ms_currentAccumulator;

// BuildAlphaGroups: GUESS(low); the callee receives the renderer, the bound, the list and the flag
BSBatchRenderer::GeometryGroup* BuildAlphaGroups(std::uint64_t a_renderer, NiBound* a_bound,
    std::uint64_t a_list, std::uint8_t a_flag);

BSShaderAccumulator* BSShaderAccumulator::GetCurrentAccumulator()
{
    return ms_currentAccumulator;
}

void BSShaderAccumulator::SetCurrentAccumulator(BSShaderAccumulator* a_accumulator)
{
    ms_currentAccumulator = a_accumulator;
}

BSBatchRenderer::GeometryGroup* BSShaderAccumulator::StartGroupingAlphas(NiBound* a_bound)
{
    return BuildAlphaGroups(unknown130, a_bound, unknown10, unknown51);
}

void BSShaderAccumulator::FinishAccumulatingPostResolveDepth(std::uint32_t flags)
{
    if (unknown150 == 0) {
        PrepareDepth();
    }
    NiAccumulator::FinishAccumulating();
}

// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis; no external implementation source reused.
// Code origin: original reconstruction from binary analysis.
// Drafted by GPT-6.1 Sol (template and generator).
// Only initialize and its EH cleanup are compared; referenced implementations are bindings.
// Object identity, signature and adapter purpose are inferred, not recovered original names.
// Labels: v2
// RVA 0x3ebb50; 63 bytes
// Origin: {"family": "storage-adapter-initializer", "template_digest": "5d5d963708e78e848f76cf2e50440ab0c4ba1d15a3d873e691883f42a0735ee8", "version": "2"}
#include "StorageInit3ebb50.h"
unsigned StorageInit3ebb50::initialize(void* object)
{
    Adapter adapter(object);
    unsigned& count = *reinterpret_cast<unsigned*>(static_cast<char*>(object) + 16);
    unsigned& storage = *reinterpret_cast<unsigned*>(static_cast<char*>(object) + 24);
    return storage_helper(&storage, &adapter, count, 16);
}

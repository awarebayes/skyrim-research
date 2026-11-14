// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis; no external implementation source reused.
// Code origin: original reconstruction from binary analysis.
// Drafted by GPT-6.1 Sol (template and generator).
// Only initialize and its EH cleanup are compared; referenced implementations are bindings.
// Object identity, signature and adapter purpose are inferred, not recovered original names.
// Labels: v2
// StorageInit1c7a20, AdapterBase, Adapter, owner, acquire, grow, release, initialize: GUESS(low) STANDIN
// storage_helper, count, storage, object: GUESS(low) STANDIN
#pragma once
struct AdapterBase {
    virtual bool acquire(unsigned, unsigned) = 0;
    virtual bool grow(unsigned, unsigned, unsigned, unsigned, unsigned) = 0;
    virtual void release() = 0;
    virtual ~AdapterBase() {}
};
struct StorageInit1c7a20;
struct Adapter : AdapterBase {
    void* owner;
    Adapter(void* object) : owner(object) {}
    bool acquire(unsigned, unsigned) override;
    bool grow(unsigned, unsigned, unsigned, unsigned, unsigned) override;
    void release() override;
    ~Adapter() override {}
};
extern unsigned storage_helper(unsigned*, AdapterBase*, unsigned, unsigned);
// No size or complete layout is asserted for caller-owned storage.
struct StorageInit1c7a20 { static unsigned initialize(void* object); };

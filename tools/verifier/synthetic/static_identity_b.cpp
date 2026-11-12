// Original synthetic TU: independent storage, despite the same local spellings as A.
struct StaticIdentityObject {
    StaticIdentityObject();
    ~StaticIdentityObject();
};
static StaticIdentityObject object;

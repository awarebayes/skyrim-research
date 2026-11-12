// Original synthetic TU: the internal initializer and teardown have the same spellings in B.
struct StaticIdentityObject {
    StaticIdentityObject();
    ~StaticIdentityObject();
};
static StaticIdentityObject object;

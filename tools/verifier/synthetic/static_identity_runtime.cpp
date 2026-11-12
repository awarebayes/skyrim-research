// Original synthetic definitions; linking both TUs must preserve their independent local objects.
struct StaticIdentityObject {
    StaticIdentityObject();
    ~StaticIdentityObject();
};
int synthetic_lifetime_count;
StaticIdentityObject::StaticIdentityObject() { ++synthetic_lifetime_count; }
StaticIdentityObject::~StaticIdentityObject() { --synthetic_lifetime_count; }
extern "C" int atexit(void (*)()) { return 0; }

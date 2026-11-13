// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103760, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103760;
extern void construct(Static103760*, const Descriptor*);
extern void destroy(Static103760*);
struct Static103760 {
    void* value;
    Static103760() { construct(this, &descriptor); }
    ~Static103760() { destroy(this); }
};

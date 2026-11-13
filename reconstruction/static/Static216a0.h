// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static216a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static216a0;
extern void construct(Static216a0*, const Descriptor*);
extern void destroy(Static216a0*);
struct Static216a0 {
    void* value;
    Static216a0() { construct(this, &descriptor); }
    ~Static216a0() { destroy(this); }
};

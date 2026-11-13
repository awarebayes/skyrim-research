// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static156a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static156a0;
extern void construct(Static156a0*, const Descriptor*);
extern void destroy(Static156a0*);
struct Static156a0 {
    void* value;
    Static156a0() { construct(this, &descriptor); }
    ~Static156a0() { destroy(this); }
};

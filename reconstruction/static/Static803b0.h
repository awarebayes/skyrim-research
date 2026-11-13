// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static803b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static803b0;
extern void construct(Static803b0*, const Descriptor*);
extern void destroy(Static803b0*);
struct Static803b0 {
    void* value;
    Static803b0() { construct(this, &descriptor); }
    ~Static803b0() { destroy(this); }
};

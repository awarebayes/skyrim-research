// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static90aa0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static90aa0;
extern void construct(Static90aa0*, const Descriptor*);
extern void destroy(Static90aa0*);
struct Static90aa0 {
    void* value;
    Static90aa0() { construct(this, &descriptor); }
    ~Static90aa0() { destroy(this); }
};

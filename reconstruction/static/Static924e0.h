// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static924e0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static924e0;
extern void construct(Static924e0*, const Descriptor*);
extern void destroy(Static924e0*);
struct Static924e0 {
    void* value;
    Static924e0() { construct(this, &descriptor); }
    ~Static924e0() { destroy(this); }
};

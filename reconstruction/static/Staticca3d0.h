// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca3d0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca3d0;
extern void construct(Staticca3d0*, const Descriptor*);
extern void destroy(Staticca3d0*);
struct Staticca3d0 {
    void* value;
    Staticca3d0() { construct(this, &descriptor); }
    ~Staticca3d0() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcabf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcabf0;
extern void construct(Staticcabf0*, const Descriptor*);
extern void destroy(Staticcabf0*);
struct Staticcabf0 {
    void* value;
    Staticcabf0() { construct(this, &descriptor); }
    ~Staticcabf0() { destroy(this); }
};

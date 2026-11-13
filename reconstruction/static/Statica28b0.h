// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica28b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica28b0;
extern void construct(Statica28b0*, const Descriptor*);
extern void destroy(Statica28b0*);
struct Statica28b0 {
    void* value;
    Statica28b0() { construct(this, &descriptor); }
    ~Statica28b0() { destroy(this); }
};

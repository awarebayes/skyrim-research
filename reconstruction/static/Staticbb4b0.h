// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb4b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb4b0;
extern void construct(Staticbb4b0*, const Descriptor*);
extern void destroy(Staticbb4b0*);
struct Staticbb4b0 {
    void* value;
    Staticbb4b0() { construct(this, &descriptor); }
    ~Staticbb4b0() { destroy(this); }
};

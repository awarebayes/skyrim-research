// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4da0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4da0;
extern void construct(Staticb4da0*, const Descriptor*);
extern void destroy(Staticb4da0*);
struct Staticb4da0 {
    void* value;
    Staticb4da0() { construct(this, &descriptor); }
    ~Staticb4da0() { destroy(this); }
};

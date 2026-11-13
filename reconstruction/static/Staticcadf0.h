// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcadf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcadf0;
extern void construct(Staticcadf0*, const Descriptor*);
extern void destroy(Staticcadf0*);
struct Staticcadf0 {
    void* value;
    Staticcadf0() { construct(this, &descriptor); }
    ~Staticcadf0() { destroy(this); }
};

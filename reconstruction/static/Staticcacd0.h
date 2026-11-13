// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcacd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcacd0;
extern void construct(Staticcacd0*, const Descriptor*);
extern void destroy(Staticcacd0*);
struct Staticcacd0 {
    void* value;
    Staticcacd0() { construct(this, &descriptor); }
    ~Staticcacd0() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef580, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef580;
extern void construct(Staticef580*, const Descriptor*);
extern void destroy(Staticef580*);
struct Staticef580 {
    void* value;
    Staticef580() { construct(this, &descriptor); }
    ~Staticef580() { destroy(this); }
};

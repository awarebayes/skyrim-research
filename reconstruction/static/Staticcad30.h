// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcad30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcad30;
extern void construct(Staticcad30*, const Descriptor*);
extern void destroy(Staticcad30*);
struct Staticcad30 {
    void* value;
    Staticcad30() { construct(this, &descriptor); }
    ~Staticcad30() { destroy(this); }
};

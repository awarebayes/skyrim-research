// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcaa40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcaa40;
extern void construct(Staticcaa40*, const Descriptor*);
extern void destroy(Staticcaa40*);
struct Staticcaa40 {
    void* value;
    Staticcaa40() { construct(this, &descriptor); }
    ~Staticcaa40() { destroy(this); }
};

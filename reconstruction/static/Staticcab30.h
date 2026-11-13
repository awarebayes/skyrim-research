// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcab30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcab30;
extern void construct(Staticcab30*, const Descriptor*);
extern void destroy(Staticcab30*);
struct Staticcab30 {
    void* value;
    Staticcab30() { construct(this, &descriptor); }
    ~Staticcab30() { destroy(this); }
};

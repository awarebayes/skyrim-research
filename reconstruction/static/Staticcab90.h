// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcab90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcab90;
extern void construct(Staticcab90*, const Descriptor*);
extern void destroy(Staticcab90*);
struct Staticcab90 {
    void* value;
    Staticcab90() { construct(this, &descriptor); }
    ~Staticcab90() { destroy(this); }
};

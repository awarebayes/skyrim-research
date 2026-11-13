// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcaa70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcaa70;
extern void construct(Staticcaa70*, const Descriptor*);
extern void destroy(Staticcaa70*);
struct Staticcaa70 {
    void* value;
    Staticcaa70() { construct(this, &descriptor); }
    ~Staticcaa70() { destroy(this); }
};

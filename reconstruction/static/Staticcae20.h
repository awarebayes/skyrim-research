// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcae20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcae20;
extern void construct(Staticcae20*, const Descriptor*);
extern void destroy(Staticcae20*);
struct Staticcae20 {
    void* value;
    Staticcae20() { construct(this, &descriptor); }
    ~Staticcae20() { destroy(this); }
};

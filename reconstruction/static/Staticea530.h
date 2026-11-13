// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticea530, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticea530;
extern void construct(Staticea530*, const Descriptor*);
extern void destroy(Staticea530*);
struct Staticea530 {
    void* value;
    Staticea530() { construct(this, &descriptor); }
    ~Staticea530() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3380, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3380;
extern void construct(Statica3380*, const Descriptor*);
extern void destroy(Statica3380*);
struct Statica3380 {
    void* value;
    Statica3380() { construct(this, &descriptor); }
    ~Statica3380() { destroy(this); }
};

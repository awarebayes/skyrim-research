// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4230, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4230;
extern void construct(Statica4230*, const Descriptor*);
extern void destroy(Statica4230*);
struct Statica4230 {
    void* value;
    Statica4230() { construct(this, &descriptor); }
    ~Statica4230() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4350, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4350;
extern void construct(Statica4350*, const Descriptor*);
extern void destroy(Statica4350*);
struct Statica4350 {
    void* value;
    Statica4350() { construct(this, &descriptor); }
    ~Statica4350() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4470, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4470;
extern void construct(Statica4470*, const Descriptor*);
extern void destroy(Statica4470*);
struct Statica4470 {
    void* value;
    Statica4470() { construct(this, &descriptor); }
    ~Statica4470() { destroy(this); }
};

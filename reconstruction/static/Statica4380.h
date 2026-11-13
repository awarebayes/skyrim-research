// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4380, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4380;
extern void construct(Statica4380*, const Descriptor*);
extern void destroy(Statica4380*);
struct Statica4380 {
    void* value;
    Statica4380() { construct(this, &descriptor); }
    ~Statica4380() { destroy(this); }
};

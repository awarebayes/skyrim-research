// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4500, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4500;
extern void construct(Statica4500*, const Descriptor*);
extern void destroy(Statica4500*);
struct Statica4500 {
    void* value;
    Statica4500() { construct(this, &descriptor); }
    ~Statica4500() { destroy(this); }
};

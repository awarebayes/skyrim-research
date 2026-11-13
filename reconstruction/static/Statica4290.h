// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4290, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4290;
extern void construct(Statica4290*, const Descriptor*);
extern void destroy(Statica4290*);
struct Statica4290 {
    void* value;
    Statica4290() { construct(this, &descriptor); }
    ~Statica4290() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4260, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4260;
extern void construct(Statica4260*, const Descriptor*);
extern void destroy(Statica4260*);
struct Statica4260 {
    void* value;
    Statica4260() { construct(this, &descriptor); }
    ~Statica4260() { destroy(this); }
};

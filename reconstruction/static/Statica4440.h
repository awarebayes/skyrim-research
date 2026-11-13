// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4440, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4440;
extern void construct(Statica4440*, const Descriptor*);
extern void destroy(Statica4440*);
struct Statica4440 {
    void* value;
    Statica4440() { construct(this, &descriptor); }
    ~Statica4440() { destroy(this); }
};

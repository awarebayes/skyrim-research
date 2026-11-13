// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4320, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4320;
extern void construct(Statica4320*, const Descriptor*);
extern void destroy(Statica4320*);
struct Statica4320 {
    void* value;
    Statica4320() { construct(this, &descriptor); }
    ~Statica4320() { destroy(this); }
};

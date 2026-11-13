// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica3410, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica3410;
extern void construct(Statica3410*, const Descriptor*);
extern void destroy(Statica3410*);
struct Statica3410 {
    void* value;
    Statica3410() { construct(this, &descriptor); }
    ~Statica3410() { destroy(this); }
};

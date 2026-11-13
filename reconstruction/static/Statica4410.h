// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4410, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4410;
extern void construct(Statica4410*, const Descriptor*);
extern void destroy(Statica4410*);
struct Statica4410 {
    void* value;
    Statica4410() { construct(this, &descriptor); }
    ~Statica4410() { destroy(this); }
};

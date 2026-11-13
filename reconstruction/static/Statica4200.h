// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica4200, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica4200;
extern void construct(Statica4200*, const Descriptor*);
extern void destroy(Statica4200*);
struct Statica4200 {
    void* value;
    Statica4200() { construct(this, &descriptor); }
    ~Statica4200() { destroy(this); }
};

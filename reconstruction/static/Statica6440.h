// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6440, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6440;
extern void construct(Statica6440*, const Descriptor*);
extern void destroy(Statica6440*);
struct Statica6440 {
    void* value;
    Statica6440() { construct(this, &descriptor); }
    ~Statica6440() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6c50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6c50;
extern void construct(Statica6c50*, const Descriptor*);
extern void destroy(Statica6c50*);
struct Statica6c50 {
    void* value;
    Statica6c50() { construct(this, &descriptor); }
    ~Statica6c50() { destroy(this); }
};

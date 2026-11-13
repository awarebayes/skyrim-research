// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6a40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6a40;
extern void construct(Statica6a40*, const Descriptor*);
extern void destroy(Statica6a40*);
struct Statica6a40 {
    void* value;
    Statica6a40() { construct(this, &descriptor); }
    ~Statica6a40() { destroy(this); }
};

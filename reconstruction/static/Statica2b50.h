// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica2b50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica2b50;
extern void construct(Statica2b50*, const Descriptor*);
extern void destroy(Statica2b50*);
struct Statica2b50 {
    void* value;
    Statica2b50() { construct(this, &descriptor); }
    ~Statica2b50() { destroy(this); }
};

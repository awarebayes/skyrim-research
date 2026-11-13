// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefe50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefe50;
extern void construct(Staticefe50*, const Descriptor*);
extern void destroy(Staticefe50*);
struct Staticefe50 {
    void* value;
    Staticefe50() { construct(this, &descriptor); }
    ~Staticefe50() { destroy(this); }
};

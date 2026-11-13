// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca010, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca010;
extern void construct(Staticca010*, const Descriptor*);
extern void destroy(Staticca010*);
struct Staticca010 {
    void* value;
    Staticca010() { construct(this, &descriptor); }
    ~Staticca010() { destroy(this); }
};

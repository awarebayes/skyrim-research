// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb100, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb100;
extern void construct(Staticbb100*, const Descriptor*);
extern void destroy(Staticbb100*);
struct Staticbb100 {
    void* value;
    Staticbb100() { construct(this, &descriptor); }
    ~Staticbb100() { destroy(this); }
};

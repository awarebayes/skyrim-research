// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb010, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb010;
extern void construct(Staticbb010*, const Descriptor*);
extern void destroy(Staticbb010*);
struct Staticbb010 {
    void* value;
    Staticbb010() { construct(this, &descriptor); }
    ~Staticbb010() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb130, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb130;
extern void construct(Staticbb130*, const Descriptor*);
extern void destroy(Staticbb130*);
struct Staticbb130 {
    void* value;
    Staticbb130() { construct(this, &descriptor); }
    ~Staticbb130() { destroy(this); }
};

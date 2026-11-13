// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb360, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb360;
extern void construct(Staticbb360*, const Descriptor*);
extern void destroy(Staticbb360*);
struct Staticbb360 {
    void* value;
    Staticbb360() { construct(this, &descriptor); }
    ~Staticbb360() { destroy(this); }
};

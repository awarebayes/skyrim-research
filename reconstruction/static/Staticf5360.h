// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf5360, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf5360;
extern void construct(Staticf5360*, const Descriptor*);
extern void destroy(Staticf5360*);
struct Staticf5360 {
    void* value;
    Staticf5360() { construct(this, &descriptor); }
    ~Staticf5360() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb190, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb190;
extern void construct(Staticbb190*, const Descriptor*);
extern void destroy(Staticbb190*);
struct Staticbb190 {
    void* value;
    Staticbb190() { construct(this, &descriptor); }
    ~Staticbb190() { destroy(this); }
};

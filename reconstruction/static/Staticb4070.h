// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4070, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4070;
extern void construct(Staticb4070*, const Descriptor*);
extern void destroy(Staticb4070*);
struct Staticb4070 {
    void* value;
    Staticb4070() { construct(this, &descriptor); }
    ~Staticb4070() { destroy(this); }
};

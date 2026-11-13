// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3f20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3f20;
extern void construct(Staticb3f20*, const Descriptor*);
extern void destroy(Staticb3f20*);
struct Staticb3f20 {
    void* value;
    Staticb3f20() { construct(this, &descriptor); }
    ~Staticb3f20() { destroy(this); }
};

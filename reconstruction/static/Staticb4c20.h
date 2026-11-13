// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4c20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4c20;
extern void construct(Staticb4c20*, const Descriptor*);
extern void destroy(Staticb4c20*);
struct Staticb4c20 {
    void* value;
    Staticb4c20() { construct(this, &descriptor); }
    ~Staticb4c20() { destroy(this); }
};

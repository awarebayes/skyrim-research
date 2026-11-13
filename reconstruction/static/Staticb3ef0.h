// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3ef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3ef0;
extern void construct(Staticb3ef0*, const Descriptor*);
extern void destroy(Staticb3ef0*);
struct Staticb3ef0 {
    void* value;
    Staticb3ef0() { construct(this, &descriptor); }
    ~Staticb3ef0() { destroy(this); }
};

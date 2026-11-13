// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf3ef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf3ef0;
extern void construct(Staticf3ef0*, const Descriptor*);
extern void destroy(Staticf3ef0*);
struct Staticf3ef0 {
    void* value;
    Staticf3ef0() { construct(this, &descriptor); }
    ~Staticf3ef0() { destroy(this); }
};

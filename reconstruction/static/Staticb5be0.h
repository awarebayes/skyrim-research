// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5be0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5be0;
extern void construct(Staticb5be0*, const Descriptor*);
extern void destroy(Staticb5be0*);
struct Staticb5be0 {
    void* value;
    Staticb5be0() { construct(this, &descriptor); }
    ~Staticb5be0() { destroy(this); }
};

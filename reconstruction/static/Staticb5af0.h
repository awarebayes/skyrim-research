// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5af0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5af0;
extern void construct(Staticb5af0*, const Descriptor*);
extern void destroy(Staticb5af0*);
struct Staticb5af0 {
    void* value;
    Staticb5af0() { construct(this, &descriptor); }
    ~Staticb5af0() { destroy(this); }
};

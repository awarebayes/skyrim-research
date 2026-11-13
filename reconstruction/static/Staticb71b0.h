// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb71b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb71b0;
extern void construct(Staticb71b0*, const Descriptor*);
extern void destroy(Staticb71b0*);
struct Staticb71b0 {
    void* value;
    Staticb71b0() { construct(this, &descriptor); }
    ~Staticb71b0() { destroy(this); }
};

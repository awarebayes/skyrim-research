// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9aa0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9aa0;
extern void construct(Staticb9aa0*, const Descriptor*);
extern void destroy(Staticb9aa0*);
struct Staticb9aa0 {
    void* value;
    Staticb9aa0() { construct(this, &descriptor); }
    ~Staticb9aa0() { destroy(this); }
};

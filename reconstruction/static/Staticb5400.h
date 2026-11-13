// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5400, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5400;
extern void construct(Staticb5400*, const Descriptor*);
extern void destroy(Staticb5400*);
struct Staticb5400 {
    void* value;
    Staticb5400() { construct(this, &descriptor); }
    ~Staticb5400() { destroy(this); }
};

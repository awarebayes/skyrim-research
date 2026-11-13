// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf1bf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf1bf0;
extern void construct(Staticf1bf0*, const Descriptor*);
extern void destroy(Staticf1bf0*);
struct Staticf1bf0 {
    void* value;
    Staticf1bf0() { construct(this, &descriptor); }
    ~Staticf1bf0() { destroy(this); }
};

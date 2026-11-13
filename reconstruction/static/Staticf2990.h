// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf2990, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf2990;
extern void construct(Staticf2990*, const Descriptor*);
extern void destroy(Staticf2990*);
struct Staticf2990 {
    void* value;
    Staticf2990() { construct(this, &descriptor); }
    ~Staticf2990() { destroy(this); }
};

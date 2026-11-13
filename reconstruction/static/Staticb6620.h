// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6620, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6620;
extern void construct(Staticb6620*, const Descriptor*);
extern void destroy(Staticb6620*);
struct Staticb6620 {
    void* value;
    Staticb6620() { construct(this, &descriptor); }
    ~Staticb6620() { destroy(this); }
};

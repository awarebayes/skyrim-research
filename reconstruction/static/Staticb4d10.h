// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4d10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4d10;
extern void construct(Staticb4d10*, const Descriptor*);
extern void destroy(Staticb4d10*);
struct Staticb4d10 {
    void* value;
    Staticb4d10() { construct(this, &descriptor); }
    ~Staticb4d10() { destroy(this); }
};

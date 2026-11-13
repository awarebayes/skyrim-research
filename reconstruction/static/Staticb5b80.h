// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5b80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5b80;
extern void construct(Staticb5b80*, const Descriptor*);
extern void destroy(Staticb5b80*);
struct Staticb5b80 {
    void* value;
    Staticb5b80() { construct(this, &descriptor); }
    ~Staticb5b80() { destroy(this); }
};

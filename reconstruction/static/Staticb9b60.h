// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9b60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9b60;
extern void construct(Staticb9b60*, const Descriptor*);
extern void destroy(Staticb9b60*);
struct Staticb9b60 {
    void* value;
    Staticb9b60() { construct(this, &descriptor); }
    ~Staticb9b60() { destroy(this); }
};

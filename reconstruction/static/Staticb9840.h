// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9840, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9840;
extern void construct(Staticb9840*, const Descriptor*);
extern void destroy(Staticb9840*);
struct Staticb9840 {
    void* value;
    Staticb9840() { construct(this, &descriptor); }
    ~Staticb9840() { destroy(this); }
};

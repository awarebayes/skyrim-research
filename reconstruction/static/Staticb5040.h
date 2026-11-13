// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5040, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5040;
extern void construct(Staticb5040*, const Descriptor*);
extern void destroy(Staticb5040*);
struct Staticb5040 {
    void* value;
    Staticb5040() { construct(this, &descriptor); }
    ~Staticb5040() { destroy(this); }
};

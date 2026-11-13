// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5e30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5e30;
extern void construct(Staticb5e30*, const Descriptor*);
extern void destroy(Staticb5e30*);
struct Staticb5e30 {
    void* value;
    Staticb5e30() { construct(this, &descriptor); }
    ~Staticb5e30() { destroy(this); }
};

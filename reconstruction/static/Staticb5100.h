// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5100, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5100;
extern void construct(Staticb5100*, const Descriptor*);
extern void destroy(Staticb5100*);
struct Staticb5100 {
    void* value;
    Staticb5100() { construct(this, &descriptor); }
    ~Staticb5100() { destroy(this); }
};

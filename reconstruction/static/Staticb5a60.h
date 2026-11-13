// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5a60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5a60;
extern void construct(Staticb5a60*, const Descriptor*);
extern void destroy(Staticb5a60*);
struct Staticb5a60 {
    void* value;
    Staticb5a60() { construct(this, &descriptor); }
    ~Staticb5a60() { destroy(this); }
};

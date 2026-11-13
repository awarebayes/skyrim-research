// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5b20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5b20;
extern void construct(Staticb5b20*, const Descriptor*);
extern void destroy(Staticb5b20*);
struct Staticb5b20 {
    void* value;
    Staticb5b20() { construct(this, &descriptor); }
    ~Staticb5b20() { destroy(this); }
};

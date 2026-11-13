// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3e00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3e00;
extern void construct(Staticb3e00*, const Descriptor*);
extern void destroy(Staticb3e00*);
struct Staticb3e00 {
    void* value;
    Staticb3e00() { construct(this, &descriptor); }
    ~Staticb3e00() { destroy(this); }
};

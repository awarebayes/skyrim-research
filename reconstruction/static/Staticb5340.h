// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5340, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5340;
extern void construct(Staticb5340*, const Descriptor*);
extern void destroy(Staticb5340*);
struct Staticb5340 {
    void* value;
    Staticb5340() { construct(this, &descriptor); }
    ~Staticb5340() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6710, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6710;
extern void construct(Staticb6710*, const Descriptor*);
extern void destroy(Staticb6710*);
struct Staticb6710 {
    void* value;
    Staticb6710() { construct(this, &descriptor); }
    ~Staticb6710() { destroy(this); }
};

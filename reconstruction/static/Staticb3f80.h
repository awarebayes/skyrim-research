// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb3f80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb3f80;
extern void construct(Staticb3f80*, const Descriptor*);
extern void destroy(Staticb3f80*);
struct Staticb3f80 {
    void* value;
    Staticb3f80() { construct(this, &descriptor); }
    ~Staticb3f80() { destroy(this); }
};

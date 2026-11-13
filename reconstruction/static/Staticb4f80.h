// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4f80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4f80;
extern void construct(Staticb4f80*, const Descriptor*);
extern void destroy(Staticb4f80*);
struct Staticb4f80 {
    void* value;
    Staticb4f80() { construct(this, &descriptor); }
    ~Staticb4f80() { destroy(this); }
};

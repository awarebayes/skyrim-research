// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6560, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6560;
extern void construct(Staticb6560*, const Descriptor*);
extern void destroy(Staticb6560*);
struct Staticb6560 {
    void* value;
    Staticb6560() { construct(this, &descriptor); }
    ~Staticb6560() { destroy(this); }
};

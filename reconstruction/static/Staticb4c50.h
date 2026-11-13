// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4c50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4c50;
extern void construct(Staticb4c50*, const Descriptor*);
extern void destroy(Staticb4c50*);
struct Staticb4c50 {
    void* value;
    Staticb4c50() { construct(this, &descriptor); }
    ~Staticb4c50() { destroy(this); }
};

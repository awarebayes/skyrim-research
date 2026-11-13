// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4e90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4e90;
extern void construct(Staticb4e90*, const Descriptor*);
extern void destroy(Staticb4e90*);
struct Staticb4e90 {
    void* value;
    Staticb4e90() { construct(this, &descriptor); }
    ~Staticb4e90() { destroy(this); }
};

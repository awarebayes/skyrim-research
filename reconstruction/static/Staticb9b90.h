// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9b90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9b90;
extern void construct(Staticb9b90*, const Descriptor*);
extern void destroy(Staticb9b90*);
struct Staticb9b90 {
    void* value;
    Staticb9b90() { construct(this, &descriptor); }
    ~Staticb9b90() { destroy(this); }
};

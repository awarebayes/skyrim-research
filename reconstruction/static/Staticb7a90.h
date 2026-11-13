// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7a90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7a90;
extern void construct(Staticb7a90*, const Descriptor*);
extern void destroy(Staticb7a90*);
struct Staticb7a90 {
    void* value;
    Staticb7a90() { construct(this, &descriptor); }
    ~Staticb7a90() { destroy(this); }
};

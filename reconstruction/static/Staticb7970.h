// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7970, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7970;
extern void construct(Staticb7970*, const Descriptor*);
extern void destroy(Staticb7970*);
struct Staticb7970 {
    void* value;
    Staticb7970() { construct(this, &descriptor); }
    ~Staticb7970() { destroy(this); }
};

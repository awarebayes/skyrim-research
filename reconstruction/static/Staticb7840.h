// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7840, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7840;
extern void construct(Staticb7840*, const Descriptor*);
extern void destroy(Staticb7840*);
struct Staticb7840 {
    void* value;
    Staticb7840() { construct(this, &descriptor); }
    ~Staticb7840() { destroy(this); }
};

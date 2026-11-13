// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7060, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7060;
extern void construct(Staticb7060*, const Descriptor*);
extern void destroy(Staticb7060*);
struct Staticb7060 {
    void* value;
    Staticb7060() { construct(this, &descriptor); }
    ~Staticb7060() { destroy(this); }
};

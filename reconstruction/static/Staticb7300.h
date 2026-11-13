// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7300, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7300;
extern void construct(Staticb7300*, const Descriptor*);
extern void destroy(Staticb7300*);
struct Staticb7300 {
    void* value;
    Staticb7300() { construct(this, &descriptor); }
    ~Staticb7300() { destroy(this); }
};

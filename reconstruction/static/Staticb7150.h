// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7150, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7150;
extern void construct(Staticb7150*, const Descriptor*);
extern void destroy(Staticb7150*);
struct Staticb7150 {
    void* value;
    Staticb7150() { construct(this, &descriptor); }
    ~Staticb7150() { destroy(this); }
};

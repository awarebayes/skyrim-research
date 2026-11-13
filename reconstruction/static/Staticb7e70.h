// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7e70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7e70;
extern void construct(Staticb7e70*, const Descriptor*);
extern void destroy(Staticb7e70*);
struct Staticb7e70 {
    void* value;
    Staticb7e70() { construct(this, &descriptor); }
    ~Staticb7e70() { destroy(this); }
};

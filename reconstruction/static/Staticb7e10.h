// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7e10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7e10;
extern void construct(Staticb7e10*, const Descriptor*);
extern void destroy(Staticb7e10*);
struct Staticb7e10 {
    void* value;
    Staticb7e10() { construct(this, &descriptor); }
    ~Staticb7e10() { destroy(this); }
};

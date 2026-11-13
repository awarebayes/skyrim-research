// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7c10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7c10;
extern void construct(Staticb7c10*, const Descriptor*);
extern void destroy(Staticb7c10*);
struct Staticb7c10 {
    void* value;
    Staticb7c10() { construct(this, &descriptor); }
    ~Staticb7c10() { destroy(this); }
};

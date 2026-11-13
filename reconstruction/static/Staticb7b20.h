// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7b20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7b20;
extern void construct(Staticb7b20*, const Descriptor*);
extern void destroy(Staticb7b20*);
struct Staticb7b20 {
    void* value;
    Staticb7b20() { construct(this, &descriptor); }
    ~Staticb7b20() { destroy(this); }
};

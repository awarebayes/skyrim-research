// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6f70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6f70;
extern void construct(Staticb6f70*, const Descriptor*);
extern void destroy(Staticb6f70*);
struct Staticb6f70 {
    void* value;
    Staticb6f70() { construct(this, &descriptor); }
    ~Staticb6f70() { destroy(this); }
};

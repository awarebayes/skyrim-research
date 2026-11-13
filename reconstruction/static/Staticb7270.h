// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7270, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7270;
extern void construct(Staticb7270*, const Descriptor*);
extern void destroy(Staticb7270*);
struct Staticb7270 {
    void* value;
    Staticb7270() { construct(this, &descriptor); }
    ~Staticb7270() { destroy(this); }
};

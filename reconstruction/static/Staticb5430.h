// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5430, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5430;
extern void construct(Staticb5430*, const Descriptor*);
extern void destroy(Staticb5430*);
struct Staticb5430 {
    void* value;
    Staticb5430() { construct(this, &descriptor); }
    ~Staticb5430() { destroy(this); }
};

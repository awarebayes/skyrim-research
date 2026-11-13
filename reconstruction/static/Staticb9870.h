// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9870, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9870;
extern void construct(Staticb9870*, const Descriptor*);
extern void destroy(Staticb9870*);
struct Staticb9870 {
    void* value;
    Staticb9870() { construct(this, &descriptor); }
    ~Staticb9870() { destroy(this); }
};

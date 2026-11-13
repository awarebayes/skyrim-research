// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6530, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6530;
extern void construct(Staticb6530*, const Descriptor*);
extern void destroy(Staticb6530*);
struct Staticb6530 {
    void* value;
    Staticb6530() { construct(this, &descriptor); }
    ~Staticb6530() { destroy(this); }
};

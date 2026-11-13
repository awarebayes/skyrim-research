// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb97b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb97b0;
extern void construct(Staticb97b0*, const Descriptor*);
extern void destroy(Staticb97b0*);
struct Staticb97b0 {
    void* value;
    Staticb97b0() { construct(this, &descriptor); }
    ~Staticb97b0() { destroy(this); }
};

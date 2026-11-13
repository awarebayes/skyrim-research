// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb2010, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb2010;
extern void construct(Staticb2010*, const Descriptor*);
extern void destroy(Staticb2010*);
struct Staticb2010 {
    void* value;
    Staticb2010() { construct(this, &descriptor); }
    ~Staticb2010() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb2860, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb2860;
extern void construct(Staticb2860*, const Descriptor*);
extern void destroy(Staticb2860*);
struct Staticb2860 {
    void* value;
    Staticb2860() { construct(this, &descriptor); }
    ~Staticb2860() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc21b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc21b0;
extern void construct(Staticc21b0*, const Descriptor*);
extern void destroy(Staticc21b0*);
struct Staticc21b0 {
    void* value;
    Staticc21b0() { construct(this, &descriptor); }
    ~Staticc21b0() { destroy(this); }
};

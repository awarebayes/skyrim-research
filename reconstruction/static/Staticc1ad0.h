// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1ad0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1ad0;
extern void construct(Staticc1ad0*, const Descriptor*);
extern void destroy(Staticc1ad0*);
struct Staticc1ad0 {
    void* value;
    Staticc1ad0() { construct(this, &descriptor); }
    ~Staticc1ad0() { destroy(this); }
};

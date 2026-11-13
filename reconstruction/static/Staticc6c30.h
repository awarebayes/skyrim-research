// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc6c30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc6c30;
extern void construct(Staticc6c30*, const Descriptor*);
extern void destroy(Staticc6c30*);
struct Staticc6c30 {
    void* value;
    Staticc6c30() { construct(this, &descriptor); }
    ~Staticc6c30() { destroy(this); }
};

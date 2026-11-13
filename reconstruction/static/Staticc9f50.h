// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9f50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9f50;
extern void construct(Staticc9f50*, const Descriptor*);
extern void destroy(Staticc9f50*);
struct Staticc9f50 {
    void* value;
    Staticc9f50() { construct(this, &descriptor); }
    ~Staticc9f50() { destroy(this); }
};

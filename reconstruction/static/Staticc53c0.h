// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc53c0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc53c0;
extern void construct(Staticc53c0*, const Descriptor*);
extern void destroy(Staticc53c0*);
struct Staticc53c0 {
    void* value;
    Staticc53c0() { construct(this, &descriptor); }
    ~Staticc53c0() { destroy(this); }
};

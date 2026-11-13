// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc17a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc17a0;
extern void construct(Staticc17a0*, const Descriptor*);
extern void destroy(Staticc17a0*);
struct Staticc17a0 {
    void* value;
    Staticc17a0() { construct(this, &descriptor); }
    ~Staticc17a0() { destroy(this); }
};

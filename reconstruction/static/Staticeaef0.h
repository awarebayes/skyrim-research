// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticeaef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticeaef0;
extern void construct(Staticeaef0*, const Descriptor*);
extern void destroy(Staticeaef0*);
struct Staticeaef0 {
    void* value;
    Staticeaef0() { construct(this, &descriptor); }
    ~Staticeaef0() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticeeb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticeeb0;
extern void construct(Staticeeb0*, const Descriptor*);
extern void destroy(Staticeeb0*);
struct Staticeeb0 {
    void* value;
    Staticeeb0() { construct(this, &descriptor); }
    ~Staticeeb0() { destroy(this); }
};

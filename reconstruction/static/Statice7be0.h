// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice7be0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice7be0;
extern void construct(Statice7be0*, const Descriptor*);
extern void destroy(Statice7be0*);
struct Statice7be0 {
    void* value;
    Statice7be0() { construct(this, &descriptor); }
    ~Statice7be0() { destroy(this); }
};

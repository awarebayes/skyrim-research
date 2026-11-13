// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice88b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice88b0;
extern void construct(Statice88b0*, const Descriptor*);
extern void destroy(Statice88b0*);
struct Statice88b0 {
    void* value;
    Statice88b0() { construct(this, &descriptor); }
    ~Statice88b0() { destroy(this); }
};

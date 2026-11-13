// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice7f30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice7f30;
extern void construct(Statice7f30*, const Descriptor*);
extern void destroy(Statice7f30*);
struct Statice7f30 {
    void* value;
    Statice7f30() { construct(this, &descriptor); }
    ~Statice7f30() { destroy(this); }
};

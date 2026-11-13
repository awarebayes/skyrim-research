// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97810, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97810;
extern void construct(Static97810*, const Descriptor*);
extern void destroy(Static97810*);
struct Static97810 {
    void* value;
    Static97810() { construct(this, &descriptor); }
    ~Static97810() { destroy(this); }
};

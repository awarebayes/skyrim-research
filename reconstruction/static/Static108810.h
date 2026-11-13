// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108810, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108810;
extern void construct(Static108810*, const Descriptor*);
extern void destroy(Static108810*);
struct Static108810 {
    void* value;
    Static108810() { construct(this, &descriptor); }
    ~Static108810() { destroy(this); }
};

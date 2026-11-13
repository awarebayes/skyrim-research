// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97ab0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97ab0;
extern void construct(Static97ab0*, const Descriptor*);
extern void destroy(Static97ab0*);
struct Static97ab0 {
    void* value;
    Static97ab0() { construct(this, &descriptor); }
    ~Static97ab0() { destroy(this); }
};

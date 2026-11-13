// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23f30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23f30;
extern void construct(Static23f30*, const Descriptor*);
extern void destroy(Static23f30*);
struct Static23f30 {
    void* value;
    Static23f30() { construct(this, &descriptor); }
    ~Static23f30() { destroy(this); }
};

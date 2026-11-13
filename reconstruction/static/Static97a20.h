// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static97a20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static97a20;
extern void construct(Static97a20*, const Descriptor*);
extern void destroy(Static97a20*);
struct Static97a20 {
    void* value;
    Static97a20() { construct(this, &descriptor); }
    ~Static97a20() { destroy(this); }
};

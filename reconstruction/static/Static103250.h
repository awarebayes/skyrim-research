// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103250;
extern void construct(Static103250*, const Descriptor*);
extern void destroy(Static103250*);
struct Static103250 {
    void* value;
    Static103250() { construct(this, &descriptor); }
    ~Static103250() { destroy(this); }
};

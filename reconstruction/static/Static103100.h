// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103100, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103100;
extern void construct(Static103100*, const Descriptor*);
extern void destroy(Static103100*);
struct Static103100 {
    void* value;
    Static103100() { construct(this, &descriptor); }
    ~Static103100() { destroy(this); }
};

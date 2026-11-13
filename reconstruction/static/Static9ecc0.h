// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ecc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ecc0;
extern void construct(Static9ecc0*, const Descriptor*);
extern void destroy(Static9ecc0*);
struct Static9ecc0 {
    void* value;
    Static9ecc0() { construct(this, &descriptor); }
    ~Static9ecc0() { destroy(this); }
};

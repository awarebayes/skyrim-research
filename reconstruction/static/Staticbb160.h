// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb160, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb160;
extern void construct(Staticbb160*, const Descriptor*);
extern void destroy(Staticbb160*);
struct Staticbb160 {
    void* value;
    Staticbb160() { construct(this, &descriptor); }
    ~Staticbb160() { destroy(this); }
};

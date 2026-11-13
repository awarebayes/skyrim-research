// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108600, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108600;
extern void construct(Static108600*, const Descriptor*);
extern void destroy(Static108600*);
struct Static108600 {
    void* value;
    Static108600() { construct(this, &descriptor); }
    ~Static108600() { destroy(this); }
};

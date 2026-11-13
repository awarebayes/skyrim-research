// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108900, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108900;
extern void construct(Static108900*, const Descriptor*);
extern void destroy(Static108900*);
struct Static108900 {
    void* value;
    Static108900() { construct(this, &descriptor); }
    ~Static108900() { destroy(this); }
};

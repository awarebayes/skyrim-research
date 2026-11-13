// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10ba0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10ba0;
extern void construct(Static10ba0*, const Descriptor*);
extern void destroy(Static10ba0*);
struct Static10ba0 {
    void* value;
    Static10ba0() { construct(this, &descriptor); }
    ~Static10ba0() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108870, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108870;
extern void construct(Static108870*, const Descriptor*);
extern void destroy(Static108870*);
struct Static108870 {
    void* value;
    Static108870() { construct(this, &descriptor); }
    ~Static108870() { destroy(this); }
};

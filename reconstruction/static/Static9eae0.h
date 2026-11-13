// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9eae0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9eae0;
extern void construct(Static9eae0*, const Descriptor*);
extern void destroy(Static9eae0*);
struct Static9eae0 {
    void* value;
    Static9eae0() { construct(this, &descriptor); }
    ~Static9eae0() { destroy(this); }
};

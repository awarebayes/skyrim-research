// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9eea0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9eea0;
extern void construct(Static9eea0*, const Descriptor*);
extern void destroy(Static9eea0*);
struct Static9eea0 {
    void* value;
    Static9eea0() { construct(this, &descriptor); }
    ~Static9eea0() { destroy(this); }
};

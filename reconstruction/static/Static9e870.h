// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9e870, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9e870;
extern void construct(Static9e870*, const Descriptor*);
extern void destroy(Static9e870*);
struct Static9e870 {
    void* value;
    Static9e870() { construct(this, &descriptor); }
    ~Static9e870() { destroy(this); }
};

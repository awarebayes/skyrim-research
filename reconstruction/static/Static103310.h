// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103310, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103310;
extern void construct(Static103310*, const Descriptor*);
extern void destroy(Static103310*);
struct Static103310 {
    void* value;
    Static103310() { construct(this, &descriptor); }
    ~Static103310() { destroy(this); }
};

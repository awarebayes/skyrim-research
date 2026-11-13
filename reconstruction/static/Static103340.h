// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103340, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103340;
extern void construct(Static103340*, const Descriptor*);
extern void destroy(Static103340*);
struct Static103340 {
    void* value;
    Static103340() { construct(this, &descriptor); }
    ~Static103340() { destroy(this); }
};

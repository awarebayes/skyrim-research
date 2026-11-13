// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109bf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109bf0;
extern void construct(Static109bf0*, const Descriptor*);
extern void destroy(Static109bf0*);
struct Static109bf0 {
    void* value;
    Static109bf0() { construct(this, &descriptor); }
    ~Static109bf0() { destroy(this); }
};

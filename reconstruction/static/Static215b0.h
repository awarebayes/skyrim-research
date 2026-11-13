// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static215b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static215b0;
extern void construct(Static215b0*, const Descriptor*);
extern void destroy(Static215b0*);
struct Static215b0 {
    void* value;
    Static215b0() { construct(this, &descriptor); }
    ~Static215b0() { destroy(this); }
};

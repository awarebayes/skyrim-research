// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static100fc0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static100fc0;
extern void construct(Static100fc0*, const Descriptor*);
extern void destroy(Static100fc0*);
struct Static100fc0 {
    void* value;
    Static100fc0() { construct(this, &descriptor); }
    ~Static100fc0() { destroy(this); }
};

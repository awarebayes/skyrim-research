// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static100cf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static100cf0;
extern void construct(Static100cf0*, const Descriptor*);
extern void destroy(Static100cf0*);
struct Static100cf0 {
    void* value;
    Static100cf0() { construct(this, &descriptor); }
    ~Static100cf0() { destroy(this); }
};

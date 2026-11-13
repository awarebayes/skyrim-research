// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static180a0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static180a0;
extern void construct(Static180a0*, const Descriptor*);
extern void destroy(Static180a0*);
struct Static180a0 {
    void* value;
    Static180a0() { construct(this, &descriptor); }
    ~Static180a0() { destroy(this); }
};

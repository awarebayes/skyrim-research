// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1aef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1aef0;
extern void construct(Static1aef0*, const Descriptor*);
extern void destroy(Static1aef0*);
struct Static1aef0 {
    void* value;
    Static1aef0() { construct(this, &descriptor); }
    ~Static1aef0() { destroy(this); }
};

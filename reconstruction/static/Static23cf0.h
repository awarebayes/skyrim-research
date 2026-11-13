// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23cf0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23cf0;
extern void construct(Static23cf0*, const Descriptor*);
extern void destroy(Static23cf0*);
struct Static23cf0 {
    void* value;
    Static23cf0() { construct(this, &descriptor); }
    ~Static23cf0() { destroy(this); }
};

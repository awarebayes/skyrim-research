// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109c20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109c20;
extern void construct(Static109c20*, const Descriptor*);
extern void destroy(Static109c20*);
struct Static109c20 {
    void* value;
    Static109c20() { construct(this, &descriptor); }
    ~Static109c20() { destroy(this); }
};

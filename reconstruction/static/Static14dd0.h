// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14dd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14dd0;
extern void construct(Static14dd0*, const Descriptor*);
extern void destroy(Static14dd0*);
struct Static14dd0 {
    void* value;
    Static14dd0() { construct(this, &descriptor); }
    ~Static14dd0() { destroy(this); }
};

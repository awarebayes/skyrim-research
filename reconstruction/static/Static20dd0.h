// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20dd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20dd0;
extern void construct(Static20dd0*, const Descriptor*);
extern void destroy(Static20dd0*);
struct Static20dd0 {
    void* value;
    Static20dd0() { construct(this, &descriptor); }
    ~Static20dd0() { destroy(this); }
};

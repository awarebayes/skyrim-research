// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23d20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23d20;
extern void construct(Static23d20*, const Descriptor*);
extern void destroy(Static23d20*);
struct Static23d20 {
    void* value;
    Static23d20() { construct(this, &descriptor); }
    ~Static23d20() { destroy(this); }
};

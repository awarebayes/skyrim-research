// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15040, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15040;
extern void construct(Static15040*, const Descriptor*);
extern void destroy(Static15040*);
struct Static15040 {
    void* value;
    Static15040() { construct(this, &descriptor); }
    ~Static15040() { destroy(this); }
};

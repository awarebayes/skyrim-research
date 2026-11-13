// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15100, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15100;
extern void construct(Static15100*, const Descriptor*);
extern void destroy(Static15100*);
struct Static15100 {
    void* value;
    Static15100() { construct(this, &descriptor); }
    ~Static15100() { destroy(this); }
};

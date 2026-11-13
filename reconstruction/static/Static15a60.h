// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15a60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15a60;
extern void construct(Static15a60*, const Descriptor*);
extern void destroy(Static15a60*);
struct Static15a60 {
    void* value;
    Static15a60() { construct(this, &descriptor); }
    ~Static15a60() { destroy(this); }
};

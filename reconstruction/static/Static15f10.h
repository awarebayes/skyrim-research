// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15f10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15f10;
extern void construct(Static15f10*, const Descriptor*);
extern void destroy(Static15f10*);
struct Static15f10 {
    void* value;
    Static15f10() { construct(this, &descriptor); }
    ~Static15f10() { destroy(this); }
};

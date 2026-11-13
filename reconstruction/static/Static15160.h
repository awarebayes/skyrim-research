// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15160, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15160;
extern void construct(Static15160*, const Descriptor*);
extern void destroy(Static15160*);
struct Static15160 {
    void* value;
    Static15160() { construct(this, &descriptor); }
    ~Static15160() { destroy(this); }
};

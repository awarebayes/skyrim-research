// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15700, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15700;
extern void construct(Static15700*, const Descriptor*);
extern void destroy(Static15700*);
struct Static15700 {
    void* value;
    Static15700() { construct(this, &descriptor); }
    ~Static15700() { destroy(this); }
};

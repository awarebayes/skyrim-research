// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15610, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15610;
extern void construct(Static15610*, const Descriptor*);
extern void destroy(Static15610*);
struct Static15610 {
    void* value;
    Static15610() { construct(this, &descriptor); }
    ~Static15610() { destroy(this); }
};

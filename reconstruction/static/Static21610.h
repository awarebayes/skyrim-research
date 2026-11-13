// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21610, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21610;
extern void construct(Static21610*, const Descriptor*);
extern void destroy(Static21610*);
struct Static21610 {
    void* value;
    Static21610() { construct(this, &descriptor); }
    ~Static21610() { destroy(this); }
};

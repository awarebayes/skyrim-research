// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21820, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21820;
extern void construct(Static21820*, const Descriptor*);
extern void destroy(Static21820*);
struct Static21820 {
    void* value;
    Static21820() { construct(this, &descriptor); }
    ~Static21820() { destroy(this); }
};

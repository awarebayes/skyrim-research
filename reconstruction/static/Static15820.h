// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15820, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15820;
extern void construct(Static15820*, const Descriptor*);
extern void destroy(Static15820*);
struct Static15820 {
    void* value;
    Static15820() { construct(this, &descriptor); }
    ~Static15820() { destroy(this); }
};

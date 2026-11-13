// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static92790, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static92790;
extern void construct(Static92790*, const Descriptor*);
extern void destroy(Static92790*);
struct Static92790 {
    void* value;
    Static92790() { construct(this, &descriptor); }
    ~Static92790() { destroy(this); }
};

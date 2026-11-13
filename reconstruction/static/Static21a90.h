// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21a90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21a90;
extern void construct(Static21a90*, const Descriptor*);
extern void destroy(Static21a90*);
struct Static21a90 {
    void* value;
    Static21a90() { construct(this, &descriptor); }
    ~Static21a90() { destroy(this); }
};

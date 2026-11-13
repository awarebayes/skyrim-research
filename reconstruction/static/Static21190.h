// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21190, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21190;
extern void construct(Static21190*, const Descriptor*);
extern void destroy(Static21190*);
struct Static21190 {
    void* value;
    Static21190() { construct(this, &descriptor); }
    ~Static21190() { destroy(this); }
};

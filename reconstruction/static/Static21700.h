// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21700, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21700;
extern void construct(Static21700*, const Descriptor*);
extern void destroy(Static21700*);
struct Static21700 {
    void* value;
    Static21700() { construct(this, &descriptor); }
    ~Static21700() { destroy(this); }
};

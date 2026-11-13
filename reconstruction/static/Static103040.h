// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103040, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103040;
extern void construct(Static103040*, const Descriptor*);
extern void destroy(Static103040*);
struct Static103040 {
    void* value;
    Static103040() { construct(this, &descriptor); }
    ~Static103040() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103670, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103670;
extern void construct(Static103670*, const Descriptor*);
extern void destroy(Static103670*);
struct Static103670 {
    void* value;
    Static103670() { construct(this, &descriptor); }
    ~Static103670() { destroy(this); }
};

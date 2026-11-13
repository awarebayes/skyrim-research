// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ab70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ab70;
extern void construct(Static9ab70*, const Descriptor*);
extern void destroy(Static9ab70*);
struct Static9ab70 {
    void* value;
    Static9ab70() { construct(this, &descriptor); }
    ~Static9ab70() { destroy(this); }
};

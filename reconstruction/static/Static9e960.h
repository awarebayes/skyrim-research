// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9e960, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9e960;
extern void construct(Static9e960*, const Descriptor*);
extern void destroy(Static9e960*);
struct Static9e960 {
    void* value;
    Static9e960() { construct(this, &descriptor); }
    ~Static9e960() { destroy(this); }
};

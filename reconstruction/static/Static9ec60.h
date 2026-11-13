// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ec60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ec60;
extern void construct(Static9ec60*, const Descriptor*);
extern void destroy(Static9ec60*);
struct Static9ec60 {
    void* value;
    Static9ec60() { construct(this, &descriptor); }
    ~Static9ec60() { destroy(this); }
};

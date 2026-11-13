// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ec30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ec30;
extern void construct(Static9ec30*, const Descriptor*);
extern void destroy(Static9ec30*);
struct Static9ec30 {
    void* value;
    Static9ec30() { construct(this, &descriptor); }
    ~Static9ec30() { destroy(this); }
};

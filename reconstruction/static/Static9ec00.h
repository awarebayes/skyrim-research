// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ec00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ec00;
extern void construct(Static9ec00*, const Descriptor*);
extern void destroy(Static9ec00*);
struct Static9ec00 {
    void* value;
    Static9ec00() { construct(this, &descriptor); }
    ~Static9ec00() { destroy(this); }
};

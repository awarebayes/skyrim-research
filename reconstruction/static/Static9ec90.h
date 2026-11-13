// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ec90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ec90;
extern void construct(Static9ec90*, const Descriptor*);
extern void destroy(Static9ec90*);
struct Static9ec90 {
    void* value;
    Static9ec90() { construct(this, &descriptor); }
    ~Static9ec90() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fa90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fa90;
extern void construct(Static9fa90*, const Descriptor*);
extern void destroy(Static9fa90*);
struct Static9fa90 {
    void* value;
    Static9fa90() { construct(this, &descriptor); }
    ~Static9fa90() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ef90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ef90;
extern void construct(Static9ef90*, const Descriptor*);
extern void destroy(Static9ef90*);
struct Static9ef90 {
    void* value;
    Static9ef90() { construct(this, &descriptor); }
    ~Static9ef90() { destroy(this); }
};

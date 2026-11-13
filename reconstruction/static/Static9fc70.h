// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fc70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fc70;
extern void construct(Static9fc70*, const Descriptor*);
extern void destroy(Static9fc70*);
struct Static9fc70 {
    void* value;
    Static9fc70() { construct(this, &descriptor); }
    ~Static9fc70() { destroy(this); }
};

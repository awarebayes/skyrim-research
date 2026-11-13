// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fb50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fb50;
extern void construct(Static9fb50*, const Descriptor*);
extern void destroy(Static9fb50*);
struct Static9fb50 {
    void* value;
    Static9fb50() { construct(this, &descriptor); }
    ~Static9fb50() { destroy(this); }
};

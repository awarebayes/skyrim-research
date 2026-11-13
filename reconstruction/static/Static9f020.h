// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9f020, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9f020;
extern void construct(Static9f020*, const Descriptor*);
extern void destroy(Static9f020*);
struct Static9f020 {
    void* value;
    Static9f020() { construct(this, &descriptor); }
    ~Static9f020() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9e750, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9e750;
extern void construct(Static9e750*, const Descriptor*);
extern void destroy(Static9e750*);
struct Static9e750 {
    void* value;
    Static9e750() { construct(this, &descriptor); }
    ~Static9e750() { destroy(this); }
};

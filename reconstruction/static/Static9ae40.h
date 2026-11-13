// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ae40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ae40;
extern void construct(Static9ae40*, const Descriptor*);
extern void destroy(Static9ae40*);
struct Static9ae40 {
    void* value;
    Static9ae40() { construct(this, &descriptor); }
    ~Static9ae40() { destroy(this); }
};

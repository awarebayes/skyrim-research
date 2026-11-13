// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9fc40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9fc40;
extern void construct(Static9fc40*, const Descriptor*);
extern void destroy(Static9fc40*);
struct Static9fc40 {
    void* value;
    Static9fc40() { construct(this, &descriptor); }
    ~Static9fc40() { destroy(this); }
};

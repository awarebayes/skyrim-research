// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9f490, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9f490;
extern void construct(Static9f490*, const Descriptor*);
extern void destroy(Static9f490*);
struct Static9f490 {
    void* value;
    Static9f490() { construct(this, &descriptor); }
    ~Static9f490() { destroy(this); }
};

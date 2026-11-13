// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9ee10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9ee10;
extern void construct(Static9ee10*, const Descriptor*);
extern void destroy(Static9ee10*);
struct Static9ee10 {
    void* value;
    Static9ee10() { construct(this, &descriptor); }
    ~Static9ee10() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109a40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109a40;
extern void construct(Static109a40*, const Descriptor*);
extern void destroy(Static109a40*);
struct Static109a40 {
    void* value;
    Static109a40() { construct(this, &descriptor); }
    ~Static109a40() { destroy(this); }
};

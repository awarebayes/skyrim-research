// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static81f40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static81f40;
extern void construct(Static81f40*, const Descriptor*);
extern void destroy(Static81f40*);
struct Static81f40 {
    void* value;
    Static81f40() { construct(this, &descriptor); }
    ~Static81f40() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static81f10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static81f10;
extern void construct(Static81f10*, const Descriptor*);
extern void destroy(Static81f10*);
struct Static81f10 {
    void* value;
    Static81f10() { construct(this, &descriptor); }
    ~Static81f10() { destroy(this); }
};

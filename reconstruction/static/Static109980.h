// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109980, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109980;
extern void construct(Static109980*, const Descriptor*);
extern void destroy(Static109980*);
struct Static109980 {
    void* value;
    Static109980() { construct(this, &descriptor); }
    ~Static109980() { destroy(this); }
};

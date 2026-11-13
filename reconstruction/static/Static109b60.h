// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109b60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109b60;
extern void construct(Static109b60*, const Descriptor*);
extern void destroy(Static109b60*);
struct Static109b60 {
    void* value;
    Static109b60() { construct(this, &descriptor); }
    ~Static109b60() { destroy(this); }
};

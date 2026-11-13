// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static21400, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static21400;
extern void construct(Static21400*, const Descriptor*);
extern void destroy(Static21400*);
struct Static21400 {
    void* value;
    Static21400() { construct(this, &descriptor); }
    ~Static21400() { destroy(this); }
};

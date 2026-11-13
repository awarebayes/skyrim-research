// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14d10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14d10;
extern void construct(Static14d10*, const Descriptor*);
extern void destroy(Static14d10*);
struct Static14d10 {
    void* value;
    Static14d10() { construct(this, &descriptor); }
    ~Static14d10() { destroy(this); }
};

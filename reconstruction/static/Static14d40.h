// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static14d40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static14d40;
extern void construct(Static14d40*, const Descriptor*);
extern void destroy(Static14d40*);
struct Static14d40 {
    void* value;
    Static14d40() { construct(this, &descriptor); }
    ~Static14d40() { destroy(this); }
};

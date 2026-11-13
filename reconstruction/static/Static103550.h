// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static103550, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static103550;
extern void construct(Static103550*, const Descriptor*);
extern void destroy(Static103550*);
struct Static103550 {
    void* value;
    Static103550() { construct(this, &descriptor); }
    ~Static103550() { destroy(this); }
};

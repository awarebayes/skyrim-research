// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108780, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108780;
extern void construct(Static108780*, const Descriptor*);
extern void destroy(Static108780*);
struct Static108780 {
    void* value;
    Static108780() { construct(this, &descriptor); }
    ~Static108780() { destroy(this); }
};

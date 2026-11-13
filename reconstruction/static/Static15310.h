// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15310, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15310;
extern void construct(Static15310*, const Descriptor*);
extern void destroy(Static15310*);
struct Static15310 {
    void* value;
    Static15310() { construct(this, &descriptor); }
    ~Static15310() { destroy(this); }
};

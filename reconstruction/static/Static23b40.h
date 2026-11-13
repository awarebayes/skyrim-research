// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23b40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23b40;
extern void construct(Static23b40*, const Descriptor*);
extern void destroy(Static23b40*);
struct Static23b40 {
    void* value;
    Static23b40() { construct(this, &descriptor); }
    ~Static23b40() { destroy(this); }
};

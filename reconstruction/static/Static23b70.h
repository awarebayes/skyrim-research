// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static23b70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static23b70;
extern void construct(Static23b70*, const Descriptor*);
extern void destroy(Static23b70*);
struct Static23b70 {
    void* value;
    Static23b70() { construct(this, &descriptor); }
    ~Static23b70() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static15f70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static15f70;
extern void construct(Static15f70*, const Descriptor*);
extern void destroy(Static15f70*);
struct Static15f70 {
    void* value;
    Static15f70() { construct(this, &descriptor); }
    ~Static15f70() { destroy(this); }
};

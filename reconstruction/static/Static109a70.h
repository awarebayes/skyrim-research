// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static109a70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static109a70;
extern void construct(Static109a70*, const Descriptor*);
extern void destroy(Static109a70*);
struct Static109a70 {
    void* value;
    Static109a70() { construct(this, &descriptor); }
    ~Static109a70() { destroy(this); }
};

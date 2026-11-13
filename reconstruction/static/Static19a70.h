// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static19a70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static19a70;
extern void construct(Static19a70*, const Descriptor*);
extern void destroy(Static19a70*);
struct Static19a70 {
    void* value;
    Static19a70() { construct(this, &descriptor); }
    ~Static19a70() { destroy(this); }
};

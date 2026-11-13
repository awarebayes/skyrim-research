// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20a70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20a70;
extern void construct(Static20a70*, const Descriptor*);
extern void destroy(Static20a70*);
struct Static20a70 {
    void* value;
    Static20a70() { construct(this, &descriptor); }
    ~Static20a70() { destroy(this); }
};

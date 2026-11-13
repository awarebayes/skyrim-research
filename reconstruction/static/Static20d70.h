// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20d70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20d70;
extern void construct(Static20d70*, const Descriptor*);
extern void destroy(Static20d70*);
struct Static20d70 {
    void* value;
    Static20d70() { construct(this, &descriptor); }
    ~Static20d70() { destroy(this); }
};

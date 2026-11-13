// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20980, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20980;
extern void construct(Static20980*, const Descriptor*);
extern void destroy(Static20980*);
struct Static20980 {
    void* value;
    Static20980() { construct(this, &descriptor); }
    ~Static20980() { destroy(this); }
};

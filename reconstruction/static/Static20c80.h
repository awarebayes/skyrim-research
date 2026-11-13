// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20c80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20c80;
extern void construct(Static20c80*, const Descriptor*);
extern void destroy(Static20c80*);
struct Static20c80 {
    void* value;
    Static20c80() { construct(this, &descriptor); }
    ~Static20c80() { destroy(this); }
};

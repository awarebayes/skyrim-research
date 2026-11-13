// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20d40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20d40;
extern void construct(Static20d40*, const Descriptor*);
extern void destroy(Static20d40*);
struct Static20d40 {
    void* value;
    Static20d40() { construct(this, &descriptor); }
    ~Static20d40() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20a10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20a10;
extern void construct(Static20a10*, const Descriptor*);
extern void destroy(Static20a10*);
struct Static20a10 {
    void* value;
    Static20a10() { construct(this, &descriptor); }
    ~Static20a10() { destroy(this); }
};

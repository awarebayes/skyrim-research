// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd420, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd420;
extern void construct(Staticd420*, const Descriptor*);
extern void destroy(Staticd420*);
struct Staticd420 {
    void* value;
    Staticd420() { construct(this, &descriptor); }
    ~Staticd420() { destroy(this); }
};

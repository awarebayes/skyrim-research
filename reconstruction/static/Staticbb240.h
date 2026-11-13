// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb240, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb240;
extern void construct(Staticbb240*, const Descriptor*);
extern void destroy(Staticbb240*);
struct Staticbb240 {
    void* value;
    Staticbb240() { construct(this, &descriptor); }
    ~Staticbb240() { destroy(this); }
};

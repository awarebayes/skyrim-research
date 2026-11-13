// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb480, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb480;
extern void construct(Staticbb480*, const Descriptor*);
extern void destroy(Staticbb480*);
struct Staticbb480 {
    void* value;
    Staticbb480() { construct(this, &descriptor); }
    ~Staticbb480() { destroy(this); }
};

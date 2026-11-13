// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd480, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd480;
extern void construct(Staticd480*, const Descriptor*);
extern void destroy(Staticd480*);
struct Staticd480 {
    void* value;
    Staticd480() { construct(this, &descriptor); }
    ~Staticd480() { destroy(this); }
};

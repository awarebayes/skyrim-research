// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd930, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd930;
extern void construct(Staticd930*, const Descriptor*);
extern void destroy(Staticd930*);
struct Staticd930 {
    void* value;
    Staticd930() { construct(this, &descriptor); }
    ~Staticd930() { destroy(this); }
};

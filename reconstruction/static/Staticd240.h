// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd240, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd240;
extern void construct(Staticd240*, const Descriptor*);
extern void destroy(Staticd240*);
struct Staticd240 {
    void* value;
    Staticd240() { construct(this, &descriptor); }
    ~Staticd240() { destroy(this); }
};

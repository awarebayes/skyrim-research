// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbaf20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbaf20;
extern void construct(Staticbaf20*, const Descriptor*);
extern void destroy(Staticbaf20*);
struct Staticbaf20 {
    void* value;
    Staticbaf20() { construct(this, &descriptor); }
    ~Staticbaf20() { destroy(this); }
};

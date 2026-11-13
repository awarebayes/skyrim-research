// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbaf50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbaf50;
extern void construct(Staticbaf50*, const Descriptor*);
extern void destroy(Staticbaf50*);
struct Staticbaf50 {
    void* value;
    Staticbaf50() { construct(this, &descriptor); }
    ~Staticbaf50() { destroy(this); }
};

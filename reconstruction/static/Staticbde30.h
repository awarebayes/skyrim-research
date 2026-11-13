// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbde30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbde30;
extern void construct(Staticbde30*, const Descriptor*);
extern void destroy(Staticbde30*);
struct Staticbde30 {
    void* value;
    Staticbde30() { construct(this, &descriptor); }
    ~Staticbde30() { destroy(this); }
};

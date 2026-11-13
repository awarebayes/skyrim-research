// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbae60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbae60;
extern void construct(Staticbae60*, const Descriptor*);
extern void destroy(Staticbae60*);
struct Staticbae60 {
    void* value;
    Staticbae60() { construct(this, &descriptor); }
    ~Staticbae60() { destroy(this); }
};

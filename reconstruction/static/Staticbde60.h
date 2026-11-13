// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbde60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbde60;
extern void construct(Staticbde60*, const Descriptor*);
extern void destroy(Staticbde60*);
struct Staticbde60 {
    void* value;
    Staticbde60() { construct(this, &descriptor); }
    ~Staticbde60() { destroy(this); }
};

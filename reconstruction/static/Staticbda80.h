// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbda80, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbda80;
extern void construct(Staticbda80*, const Descriptor*);
extern void destroy(Staticbda80*);
struct Staticbda80 {
    void* value;
    Staticbda80() { construct(this, &descriptor); }
    ~Staticbda80() { destroy(this); }
};

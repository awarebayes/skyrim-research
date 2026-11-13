// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbdd10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbdd10;
extern void construct(Staticbdd10*, const Descriptor*);
extern void destroy(Staticbdd10*);
struct Staticbdd10 {
    void* value;
    Staticbdd10() { construct(this, &descriptor); }
    ~Staticbdd10() { destroy(this); }
};

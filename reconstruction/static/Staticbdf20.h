// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbdf20, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbdf20;
extern void construct(Staticbdf20*, const Descriptor*);
extern void destroy(Staticbdf20*);
struct Staticbdf20 {
    void* value;
    Staticbdf20() { construct(this, &descriptor); }
    ~Staticbdf20() { destroy(this); }
};

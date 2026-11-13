// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticba830, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticba830;
extern void construct(Staticba830*, const Descriptor*);
extern void destroy(Staticba830*);
struct Staticba830 {
    void* value;
    Staticba830() { construct(this, &descriptor); }
    ~Staticba830() { destroy(this); }
};

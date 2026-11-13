// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticba710, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticba710;
extern void construct(Staticba710*, const Descriptor*);
extern void destroy(Staticba710*);
struct Staticba710 {
    void* value;
    Staticba710() { construct(this, &descriptor); }
    ~Staticba710() { destroy(this); }
};

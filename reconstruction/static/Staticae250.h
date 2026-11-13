// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticae250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticae250;
extern void construct(Staticae250*, const Descriptor*);
extern void destroy(Staticae250*);
struct Staticae250 {
    void* value;
    Staticae250() { construct(this, &descriptor); }
    ~Staticae250() { destroy(this); }
};

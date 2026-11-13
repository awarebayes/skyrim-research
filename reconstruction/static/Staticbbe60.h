// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbbe60, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbbe60;
extern void construct(Staticbbe60*, const Descriptor*);
extern void destroy(Staticbbe60*);
struct Staticbbe60 {
    void* value;
    Staticbbe60() { construct(this, &descriptor); }
    ~Staticbbe60() { destroy(this); }
};

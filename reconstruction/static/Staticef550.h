// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef550, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef550;
extern void construct(Staticef550*, const Descriptor*);
extern void destroy(Staticef550*);
struct Staticef550 {
    void* value;
    Staticef550() { construct(this, &descriptor); }
    ~Staticef550() { destroy(this); }
};

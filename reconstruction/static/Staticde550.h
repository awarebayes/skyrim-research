// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticde550, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticde550;
extern void construct(Staticde550*, const Descriptor*);
extern void destroy(Staticde550*);
struct Staticde550 {
    void* value;
    Staticde550() { construct(this, &descriptor); }
    ~Staticde550() { destroy(this); }
};

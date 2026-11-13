// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefa90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefa90;
extern void construct(Staticefa90*, const Descriptor*);
extern void destroy(Staticefa90*);
struct Staticefa90 {
    void* value;
    Staticefa90() { construct(this, &descriptor); }
    ~Staticefa90() { destroy(this); }
};

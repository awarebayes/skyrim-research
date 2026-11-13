// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefa30, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefa30;
extern void construct(Staticefa30*, const Descriptor*);
extern void destroy(Staticefa30*);
struct Staticefa30 {
    void* value;
    Staticefa30() { construct(this, &descriptor); }
    ~Staticefa30() { destroy(this); }
};

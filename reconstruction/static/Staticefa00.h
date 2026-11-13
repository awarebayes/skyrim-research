// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticefa00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticefa00;
extern void construct(Staticefa00*, const Descriptor*);
extern void destroy(Staticefa00*);
struct Staticefa00 {
    void* value;
    Staticefa00() { construct(this, &descriptor); }
    ~Staticefa00() { destroy(this); }
};

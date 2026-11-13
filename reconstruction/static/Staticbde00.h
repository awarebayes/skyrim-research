// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbde00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbde00;
extern void construct(Staticbde00*, const Descriptor*);
extern void destroy(Staticbde00*);
struct Staticbde00 {
    void* value;
    Staticbde00() { construct(this, &descriptor); }
    ~Staticbde00() { destroy(this); }
};

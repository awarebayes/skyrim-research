// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb4040, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb4040;
extern void construct(Staticb4040*, const Descriptor*);
extern void destroy(Staticb4040*);
struct Staticb4040 {
    void* value;
    Staticb4040() { construct(this, &descriptor); }
    ~Staticb4040() { destroy(this); }
};

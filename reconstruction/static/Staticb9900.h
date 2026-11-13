// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9900, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9900;
extern void construct(Staticb9900*, const Descriptor*);
extern void destroy(Staticb9900*);
struct Staticb9900 {
    void* value;
    Staticb9900() { construct(this, &descriptor); }
    ~Staticb9900() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd900, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd900;
extern void construct(Staticd900*, const Descriptor*);
extern void destroy(Staticd900*);
struct Staticd900 {
    void* value;
    Staticd900() { construct(this, &descriptor); }
    ~Staticd900() { destroy(this); }
};

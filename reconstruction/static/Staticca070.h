// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca070, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca070;
extern void construct(Staticca070*, const Descriptor*);
extern void destroy(Staticca070*);
struct Staticca070 {
    void* value;
    Staticca070() { construct(this, &descriptor); }
    ~Staticca070() { destroy(this); }
};

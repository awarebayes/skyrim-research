// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf1840, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf1840;
extern void construct(Staticf1840*, const Descriptor*);
extern void destroy(Staticf1840*);
struct Staticf1840 {
    void* value;
    Staticf1840() { construct(this, &descriptor); }
    ~Staticf1840() { destroy(this); }
};

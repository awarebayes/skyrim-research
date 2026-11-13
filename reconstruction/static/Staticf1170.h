// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf1170, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf1170;
extern void construct(Staticf1170*, const Descriptor*);
extern void destroy(Staticf1170*);
struct Staticf1170 {
    void* value;
    Staticf1170() { construct(this, &descriptor); }
    ~Staticf1170() { destroy(this); }
};

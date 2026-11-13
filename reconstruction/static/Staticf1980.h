// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf1980, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf1980;
extern void construct(Staticf1980*, const Descriptor*);
extern void destroy(Staticf1980*);
struct Staticf1980 {
    void* value;
    Staticf1980() { construct(this, &descriptor); }
    ~Staticf1980() { destroy(this); }
};

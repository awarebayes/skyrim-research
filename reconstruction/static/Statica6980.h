// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica6980, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica6980;
extern void construct(Statica6980*, const Descriptor*);
extern void destroy(Statica6980*);
struct Statica6980 {
    void* value;
    Statica6980() { construct(this, &descriptor); }
    ~Statica6980() { destroy(this); }
};

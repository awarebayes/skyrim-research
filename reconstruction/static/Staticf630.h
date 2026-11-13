// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf630, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf630;
extern void construct(Staticf630*, const Descriptor*);
extern void destroy(Staticf630*);
struct Staticf630 {
    void* value;
    Staticf630() { construct(this, &descriptor); }
    ~Staticf630() { destroy(this); }
};

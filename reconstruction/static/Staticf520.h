// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf520, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf520;
extern void construct(Staticf520*, const Descriptor*);
extern void destroy(Staticf520*);
struct Staticf520 {
    void* value;
    Staticf520() { construct(this, &descriptor); }
    ~Staticf520() { destroy(this); }
};

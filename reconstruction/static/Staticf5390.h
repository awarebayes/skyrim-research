// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf5390, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf5390;
extern void construct(Staticf5390*, const Descriptor*);
extern void destroy(Staticf5390*);
struct Staticf5390 {
    void* value;
    Staticf5390() { construct(this, &descriptor); }
    ~Staticf5390() { destroy(this); }
};

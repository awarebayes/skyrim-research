// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb390, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb390;
extern void construct(Staticbb390*, const Descriptor*);
extern void destroy(Staticbb390*);
struct Staticbb390 {
    void* value;
    Staticbb390() { construct(this, &descriptor); }
    ~Staticbb390() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5390, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5390;
extern void construct(Staticc5390*, const Descriptor*);
extern void destroy(Staticc5390*);
struct Staticc5390 {
    void* value;
    Staticc5390() { construct(this, &descriptor); }
    ~Staticc5390() { destroy(this); }
};

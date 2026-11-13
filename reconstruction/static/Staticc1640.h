// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1640, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1640;
extern void construct(Staticc1640*, const Descriptor*);
extern void destroy(Staticc1640*);
struct Staticc1640 {
    void* value;
    Staticc1640() { construct(this, &descriptor); }
    ~Staticc1640() { destroy(this); }
};

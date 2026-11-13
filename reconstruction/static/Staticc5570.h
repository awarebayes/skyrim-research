// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5570, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5570;
extern void construct(Staticc5570*, const Descriptor*);
extern void destroy(Staticc5570*);
struct Staticc5570 {
    void* value;
    Staticc5570() { construct(this, &descriptor); }
    ~Staticc5570() { destroy(this); }
};

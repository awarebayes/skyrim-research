// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1b00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1b00;
extern void construct(Staticc1b00*, const Descriptor*);
extern void destroy(Staticc1b00*);
struct Staticc1b00 {
    void* value;
    Staticc1b00() { construct(this, &descriptor); }
    ~Staticc1b00() { destroy(this); }
};

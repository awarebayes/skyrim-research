// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc1550, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc1550;
extern void construct(Staticc1550*, const Descriptor*);
extern void destroy(Staticc1550*);
struct Staticc1550 {
    void* value;
    Staticc1550() { construct(this, &descriptor); }
    ~Staticc1550() { destroy(this); }
};

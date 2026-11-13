// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc2770, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc2770;
extern void construct(Staticc2770*, const Descriptor*);
extern void destroy(Staticc2770*);
struct Staticc2770 {
    void* value;
    Staticc2770() { construct(this, &descriptor); }
    ~Staticc2770() { destroy(this); }
};

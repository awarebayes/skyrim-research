// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc2710, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc2710;
extern void construct(Staticc2710*, const Descriptor*);
extern void destroy(Staticc2710*);
struct Staticc2710 {
    void* value;
    Staticc2710() { construct(this, &descriptor); }
    ~Staticc2710() { destroy(this); }
};

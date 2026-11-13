// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbd8b0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbd8b0;
extern void construct(Staticbd8b0*, const Descriptor*);
extern void destroy(Staticbd8b0*);
struct Staticbd8b0 {
    void* value;
    Staticbd8b0() { construct(this, &descriptor); }
    ~Staticbd8b0() { destroy(this); }
};

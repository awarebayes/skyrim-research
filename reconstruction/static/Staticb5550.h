// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5550, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5550;
extern void construct(Staticb5550*, const Descriptor*);
extern void destroy(Staticb5550*);
struct Staticb5550 {
    void* value;
    Staticb5550() { construct(this, &descriptor); }
    ~Staticb5550() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7390, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7390;
extern void construct(Staticb7390*, const Descriptor*);
extern void destroy(Staticb7390*);
struct Staticb7390 {
    void* value;
    Staticb7390() { construct(this, &descriptor); }
    ~Staticb7390() { destroy(this); }
};

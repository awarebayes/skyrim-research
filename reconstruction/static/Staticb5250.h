// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5250;
extern void construct(Staticb5250*, const Descriptor*);
extern void destroy(Staticb5250*);
struct Staticb5250 {
    void* value;
    Staticb5250() { construct(this, &descriptor); }
    ~Staticb5250() { destroy(this); }
};

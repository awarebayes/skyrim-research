// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6890, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6890;
extern void construct(Staticb6890*, const Descriptor*);
extern void destroy(Staticb6890*);
struct Staticb6890 {
    void* value;
    Staticb6890() { construct(this, &descriptor); }
    ~Staticb6890() { destroy(this); }
};

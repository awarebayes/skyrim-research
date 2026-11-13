// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9690, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9690;
extern void construct(Staticb9690*, const Descriptor*);
extern void destroy(Staticb9690*);
struct Staticb9690 {
    void* value;
    Staticb9690() { construct(this, &descriptor); }
    ~Staticb9690() { destroy(this); }
};

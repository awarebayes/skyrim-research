// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7690, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7690;
extern void construct(Staticb7690*, const Descriptor*);
extern void destroy(Staticb7690*);
struct Staticb7690 {
    void* value;
    Staticb7690() { construct(this, &descriptor); }
    ~Staticb7690() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7240, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7240;
extern void construct(Staticb7240*, const Descriptor*);
extern void destroy(Staticb7240*);
struct Staticb7240 {
    void* value;
    Staticb7240() { construct(this, &descriptor); }
    ~Staticb7240() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9780, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9780;
extern void construct(Staticb9780*, const Descriptor*);
extern void destroy(Staticb9780*);
struct Staticb9780 {
    void* value;
    Staticb9780() { construct(this, &descriptor); }
    ~Staticb9780() { destroy(this); }
};

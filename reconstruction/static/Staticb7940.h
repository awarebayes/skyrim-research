// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7940, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7940;
extern void construct(Staticb7940*, const Descriptor*);
extern void destroy(Staticb7940*);
struct Staticb7940 {
    void* value;
    Staticb7940() { construct(this, &descriptor); }
    ~Staticb7940() { destroy(this); }
};

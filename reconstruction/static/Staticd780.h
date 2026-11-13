// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd780, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd780;
extern void construct(Staticd780*, const Descriptor*);
extern void destroy(Staticd780*);
struct Staticd780 {
    void* value;
    Staticd780() { construct(this, &descriptor); }
    ~Staticd780() { destroy(this); }
};

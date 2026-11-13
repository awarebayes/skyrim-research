// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbd280, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbd280;
extern void construct(Staticbd280*, const Descriptor*);
extern void destroy(Staticbd280*);
struct Staticbd280 {
    void* value;
    Staticbd280() { construct(this, &descriptor); }
    ~Staticbd280() { destroy(this); }
};

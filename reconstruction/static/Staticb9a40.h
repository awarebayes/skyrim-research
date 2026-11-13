// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9a40, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9a40;
extern void construct(Staticb9a40*, const Descriptor*);
extern void destroy(Staticb9a40*);
struct Staticb9a40 {
    void* value;
    Staticb9a40() { construct(this, &descriptor); }
    ~Staticb9a40() { destroy(this); }
};

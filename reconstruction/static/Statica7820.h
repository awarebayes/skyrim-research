// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statica7820, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statica7820;
extern void construct(Statica7820*, const Descriptor*);
extern void destroy(Statica7820*);
struct Statica7820 {
    void* value;
    Statica7820() { construct(this, &descriptor); }
    ~Statica7820() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticcab00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticcab00;
extern void construct(Staticcab00*, const Descriptor*);
extern void destroy(Staticcab00*);
struct Staticcab00 {
    void* value;
    Staticcab00() { construct(this, &descriptor); }
    ~Staticcab00() { destroy(this); }
};

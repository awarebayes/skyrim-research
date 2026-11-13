// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticf0390, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticf0390;
extern void construct(Staticf0390*, const Descriptor*);
extern void destroy(Staticf0390*);
struct Staticf0390 {
    void* value;
    Staticf0390() { construct(this, &descriptor); }
    ~Staticf0390() { destroy(this); }
};

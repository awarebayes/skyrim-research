// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9450, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9450;
extern void construct(Staticb9450*, const Descriptor*);
extern void destroy(Staticb9450*);
struct Staticb9450 {
    void* value;
    Staticb9450() { construct(this, &descriptor); }
    ~Staticb9450() { destroy(this); }
};

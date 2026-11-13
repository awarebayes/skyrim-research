// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7450, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7450;
extern void construct(Staticb7450*, const Descriptor*);
extern void destroy(Staticb7450*);
struct Staticb7450 {
    void* value;
    Staticb7450() { construct(this, &descriptor); }
    ~Staticb7450() { destroy(this); }
};

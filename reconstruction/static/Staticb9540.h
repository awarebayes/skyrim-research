// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb9540, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb9540;
extern void construct(Staticb9540*, const Descriptor*);
extern void destroy(Staticb9540*);
struct Staticb9540 {
    void* value;
    Staticb9540() { construct(this, &descriptor); }
    ~Staticb9540() { destroy(this); }
};

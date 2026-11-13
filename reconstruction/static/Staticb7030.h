// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb7030, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb7030;
extern void construct(Staticb7030*, const Descriptor*);
extern void destroy(Staticb7030*);
struct Staticb7030 {
    void* value;
    Staticb7030() { construct(this, &descriptor); }
    ~Staticb7030() { destroy(this); }
};

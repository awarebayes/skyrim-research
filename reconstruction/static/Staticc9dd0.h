// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc9dd0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc9dd0;
extern void construct(Staticc9dd0*, const Descriptor*);
extern void destroy(Staticc9dd0*);
struct Staticc9dd0 {
    void* value;
    Staticc9dd0() { construct(this, &descriptor); }
    ~Staticc9dd0() { destroy(this); }
};

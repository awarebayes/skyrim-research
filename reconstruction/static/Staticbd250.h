// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbd250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbd250;
extern void construct(Staticbd250*, const Descriptor*);
extern void destroy(Staticbd250*);
struct Staticbd250 {
    void* value;
    Staticbd250() { construct(this, &descriptor); }
    ~Staticbd250() { destroy(this); }
};

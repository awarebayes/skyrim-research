// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8490, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8490;
extern void construct(Staticb8490*, const Descriptor*);
extern void destroy(Staticb8490*);
struct Staticb8490 {
    void* value;
    Staticb8490() { construct(this, &descriptor); }
    ~Staticb8490() { destroy(this); }
};

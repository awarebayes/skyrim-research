// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticef490, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticef490;
extern void construct(Staticef490*, const Descriptor*);
extern void destroy(Staticef490*);
struct Staticef490 {
    void* value;
    Staticef490() { construct(this, &descriptor); }
    ~Staticef490() { destroy(this); }
};

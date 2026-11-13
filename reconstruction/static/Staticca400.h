// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca400, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca400;
extern void construct(Staticca400*, const Descriptor*);
extern void destroy(Staticca400*);
struct Staticca400 {
    void* value;
    Staticca400() { construct(this, &descriptor); }
    ~Staticca400() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd090, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd090;
extern void construct(Staticd090*, const Descriptor*);
extern void destroy(Staticd090*);
struct Staticd090 {
    void* value;
    Staticd090() { construct(this, &descriptor); }
    ~Staticd090() { destroy(this); }
};

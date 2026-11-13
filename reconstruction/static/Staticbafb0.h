// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbafb0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbafb0;
extern void construct(Staticbafb0*, const Descriptor*);
extern void destroy(Staticbafb0*);
struct Staticbafb0 {
    void* value;
    Staticbafb0() { construct(this, &descriptor); }
    ~Staticbafb0() { destroy(this); }
};

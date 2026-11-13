// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5720, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5720;
extern void construct(Staticc5720*, const Descriptor*);
extern void destroy(Staticc5720*);
struct Staticc5720 {
    void* value;
    Staticc5720() { construct(this, &descriptor); }
    ~Staticc5720() { destroy(this); }
};

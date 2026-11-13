// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc3250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc3250;
extern void construct(Staticc3250*, const Descriptor*);
extern void destroy(Staticc3250*);
struct Staticc3250 {
    void* value;
    Staticc3250() { construct(this, &descriptor); }
    ~Staticc3250() { destroy(this); }
};

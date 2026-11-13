// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca250, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca250;
extern void construct(Staticca250*, const Descriptor*);
extern void destroy(Staticca250*);
struct Staticca250 {
    void* value;
    Staticca250() { construct(this, &descriptor); }
    ~Staticca250() { destroy(this); }
};

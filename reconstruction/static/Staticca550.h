// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca550, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca550;
extern void construct(Staticca550*, const Descriptor*);
extern void destroy(Staticca550*);
struct Staticca550 {
    void* value;
    Staticca550() { construct(this, &descriptor); }
    ~Staticca550() { destroy(this); }
};

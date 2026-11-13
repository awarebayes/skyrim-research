// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticba770, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticba770;
extern void construct(Staticba770*, const Descriptor*);
extern void destroy(Staticba770*);
struct Staticba770 {
    void* value;
    Staticba770() { construct(this, &descriptor); }
    ~Staticba770() { destroy(this); }
};

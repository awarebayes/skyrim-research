// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticba740, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticba740;
extern void construct(Staticba740*, const Descriptor*);
extern void destroy(Staticba740*);
struct Staticba740 {
    void* value;
    Staticba740() { construct(this, &descriptor); }
    ~Staticba740() { destroy(this); }
};

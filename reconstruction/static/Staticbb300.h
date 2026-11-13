// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbb300, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbb300;
extern void construct(Staticbb300*, const Descriptor*);
extern void destroy(Staticbb300*);
struct Staticbb300 {
    void* value;
    Staticbb300() { construct(this, &descriptor); }
    ~Staticbb300() { destroy(this); }
};

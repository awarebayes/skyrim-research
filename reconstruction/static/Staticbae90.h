// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbae90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbae90;
extern void construct(Staticbae90*, const Descriptor*);
extern void destroy(Staticbae90*);
struct Staticbae90 {
    void* value;
    Staticbae90() { construct(this, &descriptor); }
    ~Staticbae90() { destroy(this); }
};

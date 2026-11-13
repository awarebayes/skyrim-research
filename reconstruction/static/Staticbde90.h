// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticbde90, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticbde90;
extern void construct(Staticbde90*, const Descriptor*);
extern void destroy(Staticbde90*);
struct Staticbde90 {
    void* value;
    Staticbde90() { construct(this, &descriptor); }
    ~Staticbde90() { destroy(this); }
};

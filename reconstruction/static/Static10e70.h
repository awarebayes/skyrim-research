// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10e70, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10e70;
extern void construct(Static10e70*, const Descriptor*);
extern void destroy(Static10e70*);
struct Static10e70 {
    void* value;
    Static10e70() { construct(this, &descriptor); }
    ~Static10e70() { destroy(this); }
};

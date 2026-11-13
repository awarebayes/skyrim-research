// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10120, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10120;
extern void construct(Static10120*, const Descriptor*);
extern void destroy(Static10120*);
struct Static10120 {
    void* value;
    Static10120() { construct(this, &descriptor); }
    ~Static10120() { destroy(this); }
};

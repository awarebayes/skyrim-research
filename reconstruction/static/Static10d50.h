// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10d50, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10d50;
extern void construct(Static10d50*, const Descriptor*);
extern void destroy(Static10d50*);
struct Static10d50 {
    void* value;
    Static10d50() { construct(this, &descriptor); }
    ~Static10d50() { destroy(this); }
};

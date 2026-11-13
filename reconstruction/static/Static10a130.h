// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10a130, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10a130;
extern void construct(Static10a130*, const Descriptor*);
extern void destroy(Static10a130*);
struct Static10a130 {
    void* value;
    Static10a130() { construct(this, &descriptor); }
    ~Static10a130() { destroy(this); }
};

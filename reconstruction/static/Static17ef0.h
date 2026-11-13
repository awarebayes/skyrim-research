// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static17ef0, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static17ef0;
extern void construct(Static17ef0*, const Descriptor*);
extern void destroy(Static17ef0*);
struct Static17ef0 {
    void* value;
    Static17ef0() { construct(this, &descriptor); }
    ~Static17ef0() { destroy(this); }
};

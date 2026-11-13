// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108570, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108570;
extern void construct(Static108570*, const Descriptor*);
extern void destroy(Static108570*);
struct Static108570 {
    void* value;
    Static108570() { construct(this, &descriptor); }
    ~Static108570() { destroy(this); }
};

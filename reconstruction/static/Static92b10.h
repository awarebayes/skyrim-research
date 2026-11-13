// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static92b10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static92b10;
extern void construct(Static92b10*, const Descriptor*);
extern void destroy(Static92b10*);
struct Static92b10 {
    void* value;
    Static92b10() { construct(this, &descriptor); }
    ~Static92b10() { destroy(this); }
};

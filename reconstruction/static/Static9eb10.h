// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static9eb10, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static9eb10;
extern void construct(Static9eb10*, const Descriptor*);
extern void destroy(Static9eb10*);
struct Static9eb10 {
    void* value;
    Static9eb10() { construct(this, &descriptor); }
    ~Static9eb10() { destroy(this); }
};

// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd720, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd720;
extern void construct(Staticd720*, const Descriptor*);
extern void destroy(Staticd720*);
struct Staticd720 {
    void* value;
    Staticd720() { construct(this, &descriptor); }
    ~Staticd720() { destroy(this); }
};
